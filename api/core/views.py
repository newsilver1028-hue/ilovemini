import hashlib
import secrets
from datetime import timedelta

from django.db import transaction
from django.db.models import F, Q, Sum
from django.utils import timezone
from rest_framework import permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import ScopedRateThrottle

from .integrity import ledger_record_hash, legacy_ledger_record_hash
from .models import (
    Vehicle, LedgerEntry, Reminder, Notice, Partner, Offer, PushDevice, VehicleTransferCode,
    PartnerStaff, VehicleOwnership, AttendanceCheckin,
)
from .permissions import OwnerOrStaff, SafeMethodsOrStaff
from .serializers import VehicleSerializer, LedgerEntrySerializer, ReminderSerializer, NoticeSerializer, PartnerSerializer, OfferSerializer

class HealthView(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        return Response({"status": "ok", "service": "ilovemini-api"})


def _attendance_payload(user, today):
    rows = list(AttendanceCheckin.objects.filter(user=user).order_by("-checkin_date")[:31])
    today_row = next((row for row in rows if row.checkin_date == today), None)
    anchor = today if today_row else today - timedelta(days=1)
    streak = 0
    expected = anchor
    for row in rows:
        if row.checkin_date > expected:
            continue
        if row.checkin_date != expected:
            break
        streak += 1
        expected -= timedelta(days=1)
    balance = AttendanceCheckin.objects.filter(user=user).aggregate(total=Sum("points_awarded"))["total"] or 0
    return {
        "balance_points": balance,
        "checked_in_today": today_row is not None,
        "today_points": today_row.points_awarded if today_row else 0,
        "streak_days": streak,
        "next_bonus_in_days": 7 - (streak % 7) if streak else 7,
        "checkins": [{"date": row.checkin_date.isoformat(), "points": row.points_awarded, "streak_days": row.streak_days} for row in rows[:30]],
    }


class AttendanceView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "attendance"

    def get(self, request):
        return Response(_attendance_payload(request.user, timezone.localdate()))

    def post(self, request):
        today = timezone.localdate()
        with transaction.atomic():
            # Serialize check-in attempts for the same member to prevent concurrent duplicate awards.
            type(request.user).objects.select_for_update().get(pk=request.user.pk)
            existing = AttendanceCheckin.objects.filter(user=request.user, checkin_date=today).first()
            if existing:
                payload = _attendance_payload(request.user, today)
                payload.update({"earned_points": 0, "message": "오늘은 이미 출석했어요."})
                return Response(payload, status=status.HTTP_200_OK)
            yesterday = today - timedelta(days=1)
            previous = AttendanceCheckin.objects.filter(user=request.user, checkin_date=yesterday).first()
            streak = previous.streak_days + 1 if previous else 1
            award = 1000 + (3000 if streak % 7 == 0 else 0)
            AttendanceCheckin.objects.create(user=request.user, checkin_date=today, points_awarded=award, streak_days=streak)
        payload = _attendance_payload(request.user, today)
        payload.update({"earned_points": award, "message": f"출석 완료! {award}P를 적립했어요."})
        return Response(payload, status=status.HTTP_201_CREATED)

class VehicleViewSet(viewsets.ModelViewSet):
    serializer_class = VehicleSerializer
    permission_classes = [permissions.IsAuthenticated, OwnerOrStaff]
    throttle_scope = "vehicle_transfer"
    def get_queryset(self):
        qs = Vehicle.objects.all()
        return qs if self.request.user.is_staff else qs.filter(
            ownerships__user=self.request.user,
            ownerships__ended_at__isnull=True,
        ).distinct()
    def perform_create(self, serializer):
        with transaction.atomic():
            vehicle = serializer.save()
            VehicleOwnership.objects.create(
                vehicle=vehicle,
                user=self.request.user,
                verification_method="account_registration",
                verification_status=VehicleOwnership.VerificationStatus.USER_CLAIMED,
            )

    def destroy(self, request, *args, **kwargs):
        vehicle = self.get_object()
        with transaction.atomic():
            locked_vehicle = Vehicle.objects.select_for_update().filter(pk=vehicle.pk).first()
            if locked_vehicle is None:
                return Response({"detail": "차량을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
            if locked_vehicle.ledger_entries.filter(source=LedgerEntry.Source.PARTNER).exists():
                return Response(
                    {"detail": "협력업체 인증기록이 있는 차량은 삭제할 수 없습니다."},
                    status=status.HTTP_409_CONFLICT,
                )
            return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=["get"], url_path="maintenance-summary")
    def maintenance_summary(self, request, pk=None):
        vehicle = self.get_object()
        entries = vehicle.ledger_entries.select_related("partner")
        maintenance = entries.filter(kind__in=[LedgerEntry.Kind.SERVICE, LedgerEntry.Kind.PART]).order_by("-entry_date", "-id").first()
        pending_qs = vehicle.reminders.filter(completed_at__isnull=True)
        if not request.user.is_staff:
            pending_qs = pending_qs.filter(created_at__gte=vehicle.current_ownership.started_at)
        pending = list(pending_qs)
        today = timezone.localdate()
        current_km = vehicle.current_odometer_km
        overdue_count = sum(
            1 for row in pending
            if ((row.due_date is not None and row.due_date <= today)
                or (row.due_odometer_km is not None and current_km is not None and row.due_odometer_km <= current_km))
        )
        due_dates = [row.due_date for row in pending if row.due_date is not None]
        due_km = [row.due_odometer_km for row in pending if row.due_odometer_km is not None]
        last_maintenance = LedgerEntrySerializer(maintenance, context=self.get_serializer_context()).data if maintenance else None
        return Response({
            "vehicle_id": vehicle.pk,
            "ledger_count": entries.count(),
            "verified_record_count": entries.filter(source=LedgerEntry.Source.PARTNER).count(),
            "correction_count": entries.filter(corrects__isnull=False).count(),
            "last_maintenance": last_maintenance,
            "pending_reminder_count": len(pending),
            "overdue_reminder_count": overdue_count,
            "next_due_date": min(due_dates).isoformat() if due_dates else None,
            "next_due_odometer_km": min(due_km) if due_km else None,
        })

    class TransferCodeInput(serializers.Serializer):
        code = serializers.CharField(min_length=10, max_length=10, trim_whitespace=True)

    @action(detail=True, methods=["post"], url_path="transfer-code", throttle_classes=[ScopedRateThrottle])
    def create_transfer_code(self, request, pk=None):
        if request.user.is_staff:
            return Response({"detail": "운영자 계정으로는 차량을 인계할 수 없습니다."}, status=status.HTTP_403_FORBIDDEN)
        vehicle = self.get_object()
        if vehicle.owner_id != request.user.id:
            return Response({"detail": "내 차량만 인계할 수 있습니다."}, status=status.HTTP_403_FORBIDDEN)

        alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        now = timezone.now()
        with transaction.atomic():
            vehicle = Vehicle.objects.select_for_update().get(pk=vehicle.pk)
            if vehicle.owner_id != request.user.id:
                return Response({"detail": "차량 소유자가 변경되었습니다. 다시 확인해 주세요."}, status=status.HTTP_409_CONFLICT)
            VehicleTransferCode.objects.filter(
                vehicle=vehicle, accepted_at__isnull=True, invalidated_at__isnull=True,
            ).update(invalidated_at=now)
            while True:
                code = "".join(secrets.choice(alphabet) for _ in range(10))
                digest = hashlib.sha256(code.encode("ascii")).hexdigest()
                if not VehicleTransferCode.objects.filter(code_digest=digest).exists():
                    break
            transfer = VehicleTransferCode.objects.create(
                vehicle=vehicle,
                previous_owner=request.user,
                code_digest=digest,
                expires_at=now + timedelta(hours=24),
            )

        return Response({
            "code": code,
            "expires_at": transfer.expires_at,
            "model_name": vehicle.model_name,
            "ledger_count": vehicle.ledger_entries.count(),
            "verified_record_count": vehicle.ledger_entries.filter(source=LedgerEntry.Source.PARTNER).count(),
            "correction_count": vehicle.ledger_entries.filter(corrects__isnull=False).count(),
            "reminder_count": vehicle.reminders.count(),
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="cancel-transfer", throttle_classes=[ScopedRateThrottle])
    def cancel_transfer(self, request, pk=None):
        if request.user.is_staff:
            return Response({"detail": "운영자 계정으로는 차량 인계를 취소할 수 없습니다."}, status=status.HTTP_403_FORBIDDEN)
        vehicle = self.get_object()
        if vehicle.owner_id != request.user.id:
            return Response({"detail": "내 차량의 인계만 취소할 수 있습니다."}, status=status.HTTP_403_FORBIDDEN)
        with transaction.atomic():
            vehicle = Vehicle.objects.select_for_update().get(pk=vehicle.pk)
            if vehicle.owner_id != request.user.id:
                return Response({"detail": "차량 소유자가 변경되었습니다. 다시 확인해 주세요."}, status=status.HTTP_409_CONFLICT)
            cancelled = VehicleTransferCode.objects.filter(
                vehicle=vehicle,
                accepted_at__isnull=True,
                invalidated_at__isnull=True,
            ).update(invalidated_at=timezone.now())
        return Response({"cancelled": cancelled})

    def _find_transfer(self, code):
        digest = hashlib.sha256(code.strip().upper().encode("utf-8")).hexdigest()
        transfers = VehicleTransferCode.objects.select_related("vehicle")
        return transfers.filter(
            code_digest=digest,
            accepted_at__isnull=True,
            invalidated_at__isnull=True,
            expires_at__gt=timezone.now(),
        ).first()

    @action(detail=False, methods=["post"], url_path="preview-transfer", throttle_classes=[ScopedRateThrottle])
    def preview_transfer(self, request):
        if request.user.is_staff:
            return Response({"detail": "회원 계정에서 인계 코드를 확인해 주세요."}, status=status.HTTP_403_FORBIDDEN)
        data = self.TransferCodeInput(data=request.data)
        data.is_valid(raise_exception=True)
        transfer = self._find_transfer(data.validated_data["code"])
        if transfer is None or transfer.previous_owner_id == request.user.id or transfer.vehicle.owner_id != transfer.previous_owner_id:
            return Response({"detail": "인계 코드가 틀렸거나 만료·사용되었습니다."}, status=status.HTTP_400_BAD_REQUEST)
        vehicle = transfer.vehicle
        return Response({
            "model_name": vehicle.model_name,
            "generation": vehicle.generation,
            "model_year": vehicle.model_year,
            "current_odometer_km": vehicle.current_odometer_km,
            "ledger_count": vehicle.ledger_entries.count(),
            "verified_record_count": vehicle.ledger_entries.filter(source=LedgerEntry.Source.PARTNER).count(),
            "correction_count": vehicle.ledger_entries.filter(corrects__isnull=False).count(),
            "reminder_count": vehicle.reminders.count(),
            "expires_at": transfer.expires_at,
        })

    @action(detail=False, methods=["post"], url_path="accept-transfer", throttle_classes=[ScopedRateThrottle])
    def accept_transfer(self, request):
        if request.user.is_staff:
            return Response({"detail": "회원 계정에서 차량 인계를 진행해 주세요."}, status=status.HTTP_403_FORBIDDEN)
        data = self.TransferCodeInput(data=request.data)
        data.is_valid(raise_exception=True)
        now = timezone.now()
        pending = self._find_transfer(data.validated_data["code"])
        if pending is None:
            return Response({"detail": "인계 코드가 틀렸거나 만료·사용되었습니다."}, status=status.HTTP_400_BAD_REQUEST)
        if pending.previous_owner_id == request.user.id:
            return Response({"detail": "판매자와 구매자 계정이 달라야 합니다."}, status=status.HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            vehicle = Vehicle.objects.select_for_update().get(pk=pending.vehicle_id)
            transfer = VehicleTransferCode.objects.select_for_update().filter(
                pk=pending.pk,
                accepted_at__isnull=True,
                invalidated_at__isnull=True,
                expires_at__gt=now,
            ).first()
            if transfer is None:
                return Response({"detail": "인계 코드가 틀렸거나 만료·사용되었습니다."}, status=status.HTTP_400_BAD_REQUEST)
            if transfer.previous_owner_id == request.user.id:
                return Response({"detail": "판매자와 구매자 계정이 달라야 합니다."}, status=status.HTTP_400_BAD_REQUEST)
            if vehicle.pk != transfer.vehicle_id:
                return Response({"detail": "인계 차량 정보가 변경되었습니다."}, status=status.HTTP_409_CONFLICT)
            active_ownership = VehicleOwnership.objects.select_for_update().filter(
                vehicle=vehicle,
                user_id=transfer.previous_owner_id,
                ended_at__isnull=True,
            ).first()
            if active_ownership is None:
                transfer.invalidated_at = now
                transfer.save(update_fields=["invalidated_at"])
                return Response({"detail": "인계 전에 차량 소유자가 변경되었습니다."}, status=status.HTTP_409_CONFLICT)

            active_ownership.ended_at = now
            active_ownership.save(update_fields=["ended_at"])
            VehicleOwnership.objects.create(
                vehicle=vehicle,
                user=request.user,
                started_at=now,
                verification_method="handover_code",
                verification_status=VehicleOwnership.VerificationStatus.USER_CLAIMED,
            )
            vehicle.nickname = ""
            vehicle.passport_public = False
            vehicle.save(update_fields=["nickname", "passport_public"])
            transfer.new_owner = request.user
            transfer.accepted_at = now
            transfer.save(update_fields=["new_owner", "accepted_at"])
            VehicleTransferCode.objects.filter(
                vehicle=vehicle, accepted_at__isnull=True, invalidated_at__isnull=True,
            ).exclude(pk=transfer.pk).update(invalidated_at=now)

        return Response({"transferred": True, "vehicle": self.get_serializer(vehicle).data})

class LedgerEntryViewSet(viewsets.ModelViewSet):
    serializer_class = LedgerEntrySerializer
    permission_classes = [permissions.IsAuthenticated, OwnerOrStaff]
    throttle_scope = "verified_record"
    def get_queryset(self):
        qs = LedgerEntry.objects.select_related("vehicle")
        if not self.request.user.is_staff:
            qs = qs.filter(vehicle__ownerships__user=self.request.user, vehicle__ownerships__ended_at__isnull=True)
        vehicle_id = self.request.query_params.get("vehicle")
        return qs.filter(vehicle_id=vehicle_id) if vehicle_id else qs
    def perform_create(self, serializer):
        entry = serializer.save(source=LedgerEntry.Source.OWNER)
        if entry.odometer_km is not None and (
            entry.vehicle.current_odometer_km is None or entry.odometer_km > entry.vehicle.current_odometer_km
        ):
            entry.vehicle.current_odometer_km = entry.odometer_km
            entry.vehicle.save(update_fields=["current_odometer_km"])

    def update(self, request, *args, **kwargs):
        entry = self.get_object()
        if self.get_serializer().is_inherited(entry):
            return Response({"detail": "인계받은 이전 기록은 변경할 수 없습니다."}, status=status.HTTP_409_CONFLICT)
        if entry.source == LedgerEntry.Source.PARTNER:
            return Response({"detail": "협력업체 인증기록은 수정할 수 없습니다."}, status=status.HTTP_409_CONFLICT)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        entry = self.get_object()
        if self.get_serializer().is_inherited(entry):
            return Response({"detail": "인계받은 이전 기록은 변경할 수 없습니다."}, status=status.HTTP_409_CONFLICT)
        if entry.source == LedgerEntry.Source.PARTNER:
            return Response({"detail": "협력업체 인증기록은 삭제할 수 없습니다."}, status=status.HTTP_409_CONFLICT)
        return super().destroy(request, *args, **kwargs)

    class VerifiedRecordInput(serializers.Serializer):
        vehicle_public_id = serializers.UUIDField()
        partner = serializers.PrimaryKeyRelatedField(queryset=Partner.objects.all())
        kind = serializers.ChoiceField(choices=LedgerEntry.Kind.choices)
        entry_date = serializers.DateField(default=timezone.localdate)
        odometer_km = serializers.IntegerField(min_value=0)
        amount_krw = serializers.IntegerField(min_value=0, default=0)
        description = serializers.CharField(max_length=160)
        quantity_liters = serializers.DecimalField(max_digits=7, decimal_places=2, required=False, allow_null=True)
        part_number = serializers.CharField(max_length=120, required=False, allow_blank=True)
        evidence_url = serializers.URLField(required=False, allow_blank=True)
        corrects = serializers.PrimaryKeyRelatedField(queryset=LedgerEntry.objects.all(), required=False, allow_null=True)
        correction_reason = serializers.CharField(max_length=240, required=False, allow_blank=True)

        def validate_evidence_url(self, value):
            if value and not value.lower().startswith("https://"):
                raise serializers.ValidationError("증빙 링크는 HTTPS 주소만 등록할 수 있습니다.")
            return value

        def validate(self, attrs):
            if attrs.get("corrects") and not attrs.get("correction_reason", "").strip():
                raise serializers.ValidationError({"correction_reason": "정정 사유를 입력해 주세요."})
            return attrs

    @action(detail=False, methods=["post"], url_path="partner-verified", throttle_classes=[ScopedRateThrottle])
    def create_partner_verified(self, request):
        data = self.VerifiedRecordInput(data=request.data)
        data.is_valid(raise_exception=True)
        partner = data.validated_data["partner"]
        membership = PartnerStaff.objects.filter(
            partner=partner,
            user=request.user,
            is_active=True,
            can_verify_records=True,
            partner__is_active=True,
        ).first()
        if membership is None:
            return Response({"detail": "이 협력업체의 인증기록 발행 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)

        now = timezone.now()
        with transaction.atomic():
            vehicle = Vehicle.objects.select_for_update().filter(
                public_id=data.validated_data["vehicle_public_id"],
                status="active",
            ).first()
            if vehicle is None:
                return Response({"detail": "차량 Passport QR을 확인할 수 없거나 비활성 차량입니다."}, status=status.HTTP_400_BAD_REQUEST)
            correction = data.validated_data.get("corrects")
            if correction is not None:
                correction.refresh_from_db()
                valid_signature = bool(correction.record_hash) and (
                    ledger_record_hash(correction) == correction.record_hash
                    or (correction.source == LedgerEntry.Source.PARTNER
                        and legacy_ledger_record_hash(correction) == correction.record_hash)
                )
                if (correction.vehicle_id != vehicle.pk
                        or correction.source != LedgerEntry.Source.PARTNER
                        or correction.partner_id != partner.pk
                        or not valid_signature):
                    return Response(
                        {"detail": "같은 차량·협력업체의 정상 인증기록만 정정할 수 있습니다."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            entry = LedgerEntry.objects.create(
                vehicle=vehicle,
                kind=data.validated_data["kind"],
                entry_date=data.validated_data["entry_date"],
                odometer_km=data.validated_data["odometer_km"],
                amount_krw=data.validated_data["amount_krw"],
                description=data.validated_data["description"],
                quantity_liters=data.validated_data.get("quantity_liters"),
                source=LedgerEntry.Source.PARTNER,
                partner=partner,
                verified_by=request.user,
                verified_at=now,
                part_number=data.validated_data.get("part_number", ""),
                evidence_url=data.validated_data.get("evidence_url", ""),
                corrects=correction,
                correction_reason=data.validated_data.get("correction_reason", "").strip(),
            )
            entry.record_hash = ledger_record_hash(entry)
            entry.save(update_fields=["record_hash"])
            if entry.odometer_km is not None and (
                vehicle.current_odometer_km is None or entry.odometer_km > vehicle.current_odometer_km
            ):
                vehicle.current_odometer_km = entry.odometer_km
                vehicle.save(update_fields=["current_odometer_km"])

        return Response(self.get_serializer(entry).data, status=status.HTTP_201_CREATED)

class ReminderViewSet(viewsets.ModelViewSet):
    serializer_class = ReminderSerializer
    permission_classes = [permissions.IsAuthenticated, OwnerOrStaff]
    def get_queryset(self):
        qs = Reminder.objects.select_related("vehicle")
        if not self.request.user.is_staff:
            qs = qs.filter(vehicle__ownerships__user=self.request.user,
                           vehicle__ownerships__ended_at__isnull=True,
                           created_at__gte=F("vehicle__ownerships__started_at"))
        vehicle_id = self.request.query_params.get("vehicle")
        return qs.filter(vehicle_id=vehicle_id) if vehicle_id else qs
    def perform_update(self, serializer):
        serializer.save(notification_sent_at=None)
    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        reminder = self.get_object()
        reminder.completed_at = timezone.now()
        reminder.save(update_fields=["completed_at"])
        return Response(self.get_serializer(reminder).data)

class PushDeviceView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    class InputSerializer(serializers.Serializer):
        installation_id = serializers.CharField(max_length=128, trim_whitespace=True)
        platform = serializers.ChoiceField(choices=PushDevice.Platform.choices, required=False)

    def post(self, request):
        data = self.InputSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        installation_id = data.validated_data["installation_id"]
        platform = data.validated_data.get("platform")
        device, _ = PushDevice.objects.update_or_create(
            installation_id=installation_id,
            defaults={"user": request.user, "platform": platform or PushDevice.Platform.ANDROID},
        )
        return Response({"registered": True, "platform": device.platform}, status=status.HTTP_200_OK)

    def delete(self, request):
        data = self.InputSerializer(data=request.data, partial=True)
        data.is_valid(raise_exception=True)
        installation_id = data.validated_data.get("installation_id")
        if installation_id:
            PushDevice.objects.filter(user=request.user, installation_id=installation_id).delete()
        else:
            PushDevice.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class NoticeViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NoticeSerializer
    permission_classes = [SafeMethodsOrStaff]
    def get_queryset(self):
        now = timezone.now()
        return Notice.objects.filter(is_published=True, published_at__lte=now).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=now)
        )

class PartnerViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PartnerSerializer
    permission_classes = [SafeMethodsOrStaff]
    queryset = Partner.objects.filter(is_active=True)

    @action(detail=False, methods=["get"], url_path="my-workplaces", permission_classes=[permissions.IsAuthenticated])
    def my_workplaces(self, request):
        memberships = PartnerStaff.objects.filter(
            user=request.user, is_active=True, can_verify_records=True, partner__is_active=True,
        ).select_related("partner")
        return Response([{"id": row.partner_id, "name": row.partner.name} for row in memberships])

class OfferViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OfferSerializer
    permission_classes = [SafeMethodsOrStaff]
    def get_queryset(self):
        now = timezone.now()
        return Offer.objects.filter(is_active=True, partner__is_active=True).filter(
            Q(starts_at__isnull=True) | Q(starts_at__lte=now)
        ).filter(
            Q(ends_at__isnull=True) | Q(ends_at__gte=now)
        )
