import logging
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import (
    ClassSession,
    Classroom,
    Device,
    PairingCode,
    RemoteCommand,
    Student,
    TeacherAssignment,
)
from .permissions import DeviceTokenAuthentication, IsRegisteredDevice, can_control_class, can_control_student, is_master_owner, visible_students

logger = logging.getLogger(__name__)
COMMAND_TTL = timedelta(minutes=2)
DEVICE_STALE_AFTER = timedelta(seconds=120)


class OnClassTokenObtainPairView(TokenObtainPairView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "onclass_login"


def _send_device_wake(device, command):
    """Send metadata-only wake payload through the shared, already-configured FCM service."""
    if not device.fcm_token:
        return
    try:
        from firebase_admin import messaging
        from core.push import _ensure_firebase

        if not _ensure_firebase():
            return
        messaging.send(messaging.Message(
            token=device.fcm_token,
            data={"type": "onclass_command", "command_id": str(command.command_id)},
            android=messaging.AndroidConfig(priority="high"),
            apns=messaging.APNSConfig(headers={"apns-priority": "5"}),
        ))
    except Exception as exc:
        # Command remains in the durable queue; foreground polling is the fallback.
        logger.warning("OnClass wake notification failed (device=%s, error=%s)", device.pk, type(exc).__name__)


def _new_command(device, action, *, session=None, expires_at=None, initial_state=RemoteCommand.State.PENDING, detail=""):
    command = RemoteCommand.objects.create(
        device=device,
        session=session,
        action=action,
        state=initial_state,
        detail=detail,
        expires_at=expires_at or (timezone.now() + COMMAND_TTL),
    )
    if initial_state == RemoteCommand.State.PENDING:
        _send_device_wake(device, command)
    return command


def _student_status(student):
    now = timezone.now()
    devices = list(student.devices.filter(is_active=True).order_by("-enrolled_at"))
    if not devices:
        return {"state": "not_connected", "devices": []}
    result = []
    for device in devices:
        latest = device.commands.order_by("-created_at").first()
        if device.platform == Device.Platform.IOS:
            state = "unsupported"
        elif device.last_seen_at is None or now - device.last_seen_at > DEVICE_STALE_AFTER:
            state = "offline"
        elif latest is None:
            state = "ready" if device.permission_granted else "permission_required"
        elif latest.expires_at <= now and latest.state in (RemoteCommand.State.PENDING, RemoteCommand.State.DELIVERED):
            state = "offline"
        elif latest.state == RemoteCommand.State.PENDING or latest.state == RemoteCommand.State.DELIVERED:
            state = (
                "consent_pending" if latest.action == RemoteCommand.Action.CONSENT
                else "unlock_pending" if latest.action == RemoteCommand.Action.UNLOCK
                else "lock_pending"
            )
        elif latest.state == RemoteCommand.State.ACCEPTED:
            state = "permission_required" if not device.permission_granted else "lock_pending"
        elif latest.state == RemoteCommand.State.DECLINED:
            state = "consent_declined"
        elif latest.state == RemoteCommand.State.APPLIED:
            state = "locked" if latest.action == RemoteCommand.Action.LOCK and device.lock_active else "ready"
        elif latest.state == RemoteCommand.State.PERMISSION_REQUIRED:
            state = "permission_required"
        elif latest.state == RemoteCommand.State.UNSUPPORTED:
            state = "unsupported"
        elif latest.state == RemoteCommand.State.FAILED:
            state = "failed"
        elif latest.state == RemoteCommand.State.EXPIRED:
            state = "offline"
        else:
            state = "ready"
        result.append({
            "device_id": str(device.installation_id),
            "platform": device.platform,
            "label": device.label,
            "state": state,
            "last_seen_at": device.last_seen_at,
            "permission_granted": device.permission_granted,
            "lock_active": device.lock_active,
        })
    return {"state": result[0]["state"], "devices": result}


def _student_payload(student, active_sessions=None):
    active_sessions = active_sessions or {}
    return {
        "student_id": student.pk,
        "student_code": student.student_code,
        "display_name": student.display_name,
        "organization_id": student.organization_id,
        "organization": student.organization.name,
        "classroom_id": student.classroom_id,
        "classroom": student.classroom.name,
        "active_session_id": active_sessions.get(student.classroom_id),
        **_student_status(student),
    }


class RosterView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        students = visible_students(request.user).select_related("organization", "classroom").prefetch_related("devices__commands")
        active_sessions = {
            session.classroom_id: session.pk
            for session in ClassSession.objects.filter(
                classroom_id__in=students.values("classroom_id"),
                state=ClassSession.State.ACTIVE,
            )
        }
        return Response({"students": [_student_payload(student, active_sessions) for student in students]})


class RoleSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from .models import GuardianLink, OrganizationAdministrator

        user = request.user
        return Response({
            "email": user.email,
            "roles": {
                "master": is_master_owner(user),
                "organization_admin": OrganizationAdministrator.objects.filter(user=user).exists(),
                "teacher": TeacherAssignment.objects.filter(user=user).exists(),
                "guardian": GuardianLink.objects.filter(user=user, verified_at__isnull=False).exists(),
            },
        })


class PairingCodeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, student_id):
        student = get_object_or_404(visible_students(request.user), pk=student_id)
        if not can_control_student(request.user, student):
            return Response({"detail": "이 학생의 기기를 등록할 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)
        raw, code_hash = PairingCode.issue_code()
        PairingCode.objects.filter(student=student, used_at__isnull=True).update(used_at=timezone.now())
        PairingCode.objects.create(
            student=student,
            code_hash=code_hash,
            created_by=request.user,
            expires_at=timezone.now() + timedelta(minutes=15),
        )
        return Response({"pairing_code": raw, "expires_in_seconds": 900})


class DeviceEnrollView(APIView):
    permission_classes = [permissions.AllowAny]

    class Input(serializers.Serializer):
        pairing_code = serializers.CharField(max_length=64, trim_whitespace=True)
        platform = serializers.ChoiceField(choices=Device.Platform.choices)
        label = serializers.CharField(max_length=80, required=False, allow_blank=True)
        fcm_token = serializers.CharField(max_length=2048, required=False, allow_blank=True)

    @transaction.atomic
    def post(self, request):
        serializer = self.Input(data=request.data)
        serializer.is_valid(raise_exception=True)
        from .models import digest_secret
        code_hash = digest_secret(serializer.validated_data["pairing_code"])
        pairing = PairingCode.objects.select_for_update().filter(
            code_hash=code_hash,
            used_at__isnull=True,
            expires_at__gt=timezone.now(),
            student__is_active=True,
        ).select_related("student").first()
        if pairing is None:
            return Response({"detail": "등록 코드가 만료되었거나 이미 사용됐습니다."}, status=status.HTTP_400_BAD_REQUEST)
        pairing.used_at = timezone.now()
        pairing.save(update_fields=["used_at"])
        token, token_hash = Device.issue_token()
        device = Device.objects.create(
            student=pairing.student,
            platform=serializer.validated_data["platform"],
            device_token_hash=token_hash,
            label=serializer.validated_data.get("label", "")[:80],
            fcm_token=serializer.validated_data.get("fcm_token", ""),
            last_seen_at=timezone.now(),
        )
        return Response({"device_id": str(device.installation_id), "device_token": token}, status=status.HTTP_201_CREATED)


class DeviceEndpoint(APIView):
    authentication_classes = [DeviceTokenAuthentication]
    permission_classes = [IsRegisteredDevice]

    def get(self, request):
        device = request.user
        now = timezone.now()
        device.last_seen_at = now
        device.save(update_fields=["last_seen_at"])
        device.commands.filter(
            state=RemoteCommand.State.PENDING,
            expires_at__lte=now,
        ).update(state=RemoteCommand.State.EXPIRED)
        # Keep unacknowledged deliveries visible on the next foreground poll.
        # A one-shot PENDING-only queue silently lost commands whenever the app
        # was killed or the network dropped after marking a command delivered.
        commands = list(device.commands.filter(
            state__in=(RemoteCommand.State.PENDING, RemoteCommand.State.DELIVERED),
            expires_at__gt=now,
        ).order_by("created_at")[:20])
        now = timezone.now()
        for command in commands:
            if command.state == RemoteCommand.State.PENDING:
                command.state = RemoteCommand.State.DELIVERED
                command.save(update_fields=["state"])
        return Response({"commands": [{
            "command_id": str(command.command_id),
            "action": command.action,
            "session_id": command.session_id,
            "expires_at": command.expires_at,
        } for command in commands], "server_time": now})

    def post(self, request):
        device = request.user
        serializer = DeviceEndpoint.Report(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        device.last_seen_at = timezone.now()
        if "permission_granted" in data:
            device.permission_granted = data["permission_granted"]
        if "fcm_token" in data:
            device.fcm_token = data["fcm_token"]
        device.save(update_fields=["last_seen_at", "permission_granted", "fcm_token"])
        command = get_object_or_404(device.commands, command_id=data["command_id"])
        if command.state not in (RemoteCommand.State.PENDING, RemoteCommand.State.DELIVERED):
            return Response({"detail": "이미 처리된 명령입니다.", "state": command.state}, status=status.HTTP_409_CONFLICT)
        if command.expires_at <= timezone.now():
            command.state = RemoteCommand.State.EXPIRED
            command.save(update_fields=["state"])
            return Response({"detail": "명령이 만료됐습니다.", "state": command.state}, status=status.HTTP_410_GONE)
        outcome = data["outcome"]
        command.responded_at = timezone.now()
        command.detail = data.get("detail", "")[:240]
        if command.action == RemoteCommand.Action.CONSENT:
            if outcome == "accepted":
                command.state = RemoteCommand.State.ACCEPTED
                device.app_consent = True
                device.save(update_fields=["app_consent"])
                if command.session_id and command.session.state != ClassSession.State.ACTIVE:
                    _new_command(device, RemoteCommand.Action.LOCK, session=command.session,
                                 initial_state=RemoteCommand.State.EXPIRED,
                                 detail="수업 세션이 종료되어 잠금 명령을 만들지 않았습니다.")
                elif device.platform == Device.Platform.IOS:
                    _new_command(device, RemoteCommand.Action.LOCK, session=command.session,
                                 initial_state=RemoteCommand.State.UNSUPPORTED,
                                 detail="개인 iPhone은 학교 원격 잠금 미지원")
                elif not device.permission_granted:
                    _new_command(device, RemoteCommand.Action.LOCK, session=command.session,
                                 initial_state=RemoteCommand.State.PERMISSION_REQUIRED,
                                 detail="Android 접근성 권한 필요")
                else:
                    _new_command(device, RemoteCommand.Action.LOCK, session=command.session,
                                 expires_at=(command.session.started_at + timedelta(hours=4)) if command.session else timezone.now() + timedelta(hours=4))
            elif outcome == "declined":
                command.state = RemoteCommand.State.DECLINED
                device.app_consent = False
                device.save(update_fields=["app_consent"])
            else:
                command.state = RemoteCommand.State.FAILED
        else:
            if outcome == "applied":
                command.state = RemoteCommand.State.APPLIED
                device.lock_active = command.action == RemoteCommand.Action.LOCK
            elif outcome == "permission_required":
                command.state = RemoteCommand.State.PERMISSION_REQUIRED
                device.permission_granted = False
            elif outcome == "unsupported":
                command.state = RemoteCommand.State.UNSUPPORTED
            else:
                command.state = RemoteCommand.State.FAILED
            device.save(update_fields=["lock_active", "permission_granted"])
        command.save(update_fields=["state", "detail", "responded_at"])
        return Response({"accepted": True, "state": command.state})

    class Report(serializers.Serializer):
        command_id = serializers.UUIDField()
        outcome = serializers.ChoiceField(choices=["accepted", "declined", "applied", "permission_required", "unsupported", "failed"])
        permission_granted = serializers.BooleanField(required=False)
        fcm_token = serializers.CharField(max_length=2048, required=False, allow_blank=True)
        detail = serializers.CharField(max_length=240, required=False, allow_blank=True)


class ClassSessionStartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, classroom_id):
        classroom = get_object_or_404(Classroom.objects.select_related("organization"), pk=classroom_id, is_active=True)
        if not can_control_class(request.user, classroom):
            return Response({"detail": "이 학급을 시작할 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)
        existing = ClassSession.objects.filter(classroom=classroom, state=ClassSession.State.ACTIVE).first()
        if existing:
            return Response({"detail": "이미 진행 중인 수업이 있습니다.", "session_id": existing.pk}, status=status.HTTP_409_CONFLICT)
        session = ClassSession.objects.create(classroom=classroom, started_by=request.user)
        summaries = []
        for student in Student.objects.filter(classroom=classroom, is_active=True).prefetch_related("devices"):
            devices = list(student.devices.filter(is_active=True))
            if not devices:
                summaries.append({"student_id": student.pk, "state": "not_connected"})
                continue
            student_states = []
            for device in devices:
                if device.platform == Device.Platform.IOS:
                    student_states.append("unsupported")
                    continue
                _new_command(device, RemoteCommand.Action.CONSENT, session=session)
                student_states.append("consent_pending")
            summaries.append({"student_id": student.pk, "state": student_states[0], "devices": student_states})
        return Response({"session_id": session.pk, "state": session.state, "students": summaries}, status=status.HTTP_201_CREATED)


class StudentCommandView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, student_id):
        student = get_object_or_404(visible_students(request.user), pk=student_id, is_active=True)
        if not can_control_student(request.user, student):
            return Response({"detail": "이 학생을 관리할 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)
        serializer = self.Input(data=request.data)
        serializer.is_valid(raise_exception=True)
        action = serializer.validated_data["action"]
        devices = list(student.devices.filter(is_active=True))
        results = []
        for device in devices:
            if device.platform == Device.Platform.IOS:
                command = _new_command(device, action, initial_state=RemoteCommand.State.UNSUPPORTED,
                                       detail="개인 iPhone은 학교 원격 잠금 미지원")
            elif action == RemoteCommand.Action.LOCK:
                command = _new_command(device, RemoteCommand.Action.CONSENT)
            else:
                command = _new_command(device, action)
            results.append({"device_id": str(device.installation_id), "state": command.state})
        if not devices:
            return Response({"state": "not_connected", "devices": []}, status=status.HTTP_200_OK)
        return Response({"state": "pending", "devices": results}, status=status.HTTP_202_ACCEPTED)

    class Input(serializers.Serializer):
        action = serializers.ChoiceField(choices=[RemoteCommand.Action.LOCK, RemoteCommand.Action.UNLOCK])


class ClassSessionEndView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, session_id):
        session = get_object_or_404(ClassSession.objects.select_related("classroom__organization"), pk=session_id)
        if not can_control_class(request.user, session.classroom):
            return Response({"detail": "이 수업을 종료할 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)
        if session.state == ClassSession.State.ENDED:
            return Response({"session_id": session.pk, "state": session.state})
        session.state = ClassSession.State.ENDED
        session.ended_at = timezone.now()
        session.save(update_fields=["state", "ended_at"])
        count = 0
        for device in Device.objects.filter(student__classroom=session.classroom, is_active=True, lock_active=True):
            _new_command(device, RemoteCommand.Action.UNLOCK, session=session, expires_at=timezone.now() + COMMAND_TTL)
            count += 1
        return Response({"session_id": session.pk, "state": session.state, "unlock_commands": count})


class DeviceHeartbeatView(APIView):
    authentication_classes = [DeviceTokenAuthentication]
    permission_classes = [IsRegisteredDevice]

    class Input(serializers.Serializer):
        permission_granted = serializers.BooleanField(required=False)
        fcm_token = serializers.CharField(max_length=2048, required=False, allow_blank=True)
        label = serializers.CharField(max_length=80, required=False, allow_blank=True)

    def post(self, request):
        serializer = self.Input(data=request.data)
        serializer.is_valid(raise_exception=True)
        device = request.user
        values = serializer.validated_data
        device.last_seen_at = timezone.now()
        update_fields = ["last_seen_at"]
        if "permission_granted" in values:
            device.permission_granted = values["permission_granted"]
            update_fields.append("permission_granted")
        if "fcm_token" in values:
            device.fcm_token = values["fcm_token"]
            update_fields.append("fcm_token")
        if "label" in values:
            device.label = values["label"]
            update_fields.append("label")
        device.save(update_fields=update_fields)
        return Response({"received_at": device.last_seen_at, "permission_granted": device.permission_granted})
