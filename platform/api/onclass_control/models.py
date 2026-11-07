import hashlib
import secrets
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


def digest_secret(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class Organization(models.Model):
    class Kind(models.TextChoices):
        SCHOOL = "school", "학교"
        ACADEMY = "academy", "학원"

    name = models.CharField(max_length=120)
    kind = models.CharField(max_length=16, choices=Kind.choices)
    external_code = models.CharField(max_length=32, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name", "pk"]
        constraints = [models.UniqueConstraint(
            fields=["kind", "external_code"],
            condition=~models.Q(external_code=""),
            name="onclass_org_kind_code_uniq",
        )]

    def __str__(self):
        return self.name


class OrganizationAdministrator(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="administrators")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="onclass_organization_admins")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["organization", "user"], name="onclass_org_admin_uniq")]


class Classroom(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="classrooms")
    name = models.CharField(max_length=80)
    grade = models.CharField(max_length=20, blank=True)
    room = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["organization__name", "grade", "room", "name", "pk"]
        constraints = [models.UniqueConstraint(fields=["organization", "name"], name="onclass_class_org_name_uniq")]

    def __str__(self):
        return f"{self.organization.name} · {self.name}"


class Student(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="students")
    classroom = models.ForeignKey(Classroom, on_delete=models.PROTECT, related_name="students")
    student_code = models.CharField(max_length=48)
    display_name = models.CharField(max_length=80)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["classroom__grade", "classroom__room", "student_code", "pk"]
        constraints = [models.UniqueConstraint(fields=["organization", "student_code"], name="onclass_student_org_code_uniq")]

    def clean(self):
        if self.classroom_id and self.organization_id and self.classroom.organization_id != self.organization_id:
            raise ValidationError("학생과 학급은 같은 기관에 속해야 합니다.")

    def __str__(self):
        return f"{self.classroom.name} · {self.display_name}"


class TeacherAssignment(models.Model):
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name="teacher_assignments")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="onclass_teacher_assignments")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="onclass_teacher_assignments_created")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["classroom", "user"], name="onclass_teacher_class_user_uniq")]


class GuardianLink(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="guardian_links")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="onclass_guardian_links")
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["student", "user"], name="onclass_guardian_student_user_uniq")]


class Device(models.Model):
    class Platform(models.TextChoices):
        ANDROID = "android", "Android"
        IOS = "ios", "iOS"

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="devices")
    installation_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    @property
    def is_authenticated(self):
        # Device-token principals pass through DRF's user-based throttles too.
        return True
    platform = models.CharField(max_length=12, choices=Platform.choices)
    device_token_hash = models.CharField(max_length=64, unique=True)
    fcm_token = models.CharField(max_length=2048, blank=True)
    label = models.CharField(max_length=80, blank=True)
    app_consent = models.BooleanField(null=True, default=None)
    permission_granted = models.BooleanField(default=False)
    lock_active = models.BooleanField(default=False)
    last_seen_at = models.DateTimeField(null=True, blank=True, db_index=True)
    is_active = models.BooleanField(default=True)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["student_id", "-enrolled_at"]

    @staticmethod
    def issue_token():
        raw = secrets.token_urlsafe(32)
        return raw, digest_secret(raw)


class PairingCode(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="pairing_codes")
    code_hash = models.CharField(max_length=64, unique=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def issue_code():
        raw = secrets.token_urlsafe(8)
        return raw, digest_secret(raw)

    def __str__(self):
        return f"{self.student} · {self.expires_at:%Y-%m-%d %H:%M}"


class ClassSession(models.Model):
    class State(models.TextChoices):
        ACTIVE = "active", "진행 중"
        ENDED = "ended", "종료"

    classroom = models.ForeignKey(Classroom, on_delete=models.PROTECT, related_name="sessions")
    started_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="onclass_sessions_started")
    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True, blank=True)
    state = models.CharField(max_length=12, choices=State.choices, default=State.ACTIVE)

    class Meta:
        ordering = ["-started_at", "-pk"]


class RemoteCommand(models.Model):
    class Action(models.TextChoices):
        CONSENT = "consent", "수업 동의 요청"
        LOCK = "lock", "수업 잠금"
        UNLOCK = "unlock", "수업 해제"

    class State(models.TextChoices):
        PENDING = "pending", "응답 대기"
        DELIVERED = "delivered", "기기에 전달"
        ACCEPTED = "accepted", "동의"
        DECLINED = "declined", "거부"
        APPLIED = "applied", "적용 완료"
        PERMISSION_REQUIRED = "permission_required", "권한 필요"
        UNSUPPORTED = "unsupported", "지원 안 됨"
        FAILED = "failed", "실패"
        EXPIRED = "expired", "만료"

    command_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    session = models.ForeignKey(ClassSession, on_delete=models.CASCADE, related_name="commands", null=True, blank=True)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name="commands")
    action = models.CharField(max_length=12, choices=Action.choices)
    state = models.CharField(max_length=24, choices=State.choices, default=State.PENDING)
    detail = models.CharField(max_length=240, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(db_index=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at", "pk"]
        indexes = [models.Index(fields=["device", "state", "expires_at"], name="onclass_cmd_device_state_idx")]
