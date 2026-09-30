from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
import uuid

class Vehicle(models.Model):
    nickname = models.CharField(max_length=40, blank=True)
    model_name = models.CharField(max_length=80)
    generation = models.CharField(max_length=40, blank=True)
    manufacturer = models.CharField(max_length=80, default="MINI")
    model_year = models.PositiveSmallIntegerField(null=True, blank=True)
    first_registration_date = models.DateField(null=True, blank=True)
    vin_hash = models.CharField(max_length=64, blank=True, db_index=True)
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    passport_public = models.BooleanField(default=False)
    status = models.CharField(max_length=16, default="active")
    current_odometer_km = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.nickname or self.model_name

    @property
    def current_ownership(self):
        return self.ownerships.filter(ended_at__isnull=True, user__isnull=False).select_related("user").first()

    @property
    def owner(self):
        ownership = self.current_ownership
        return ownership.user if ownership else None

    @property
    def owner_id(self):
        ownership = self.current_ownership
        return ownership.user_id if ownership else None


class VehicleOwnership(models.Model):
    class VerificationStatus(models.TextChoices):
        USER_CLAIMED = "user_claimed", "차주 등록"
        DOCUMENT_VERIFIED = "document_verified", "서류 확인"
        SYSTEM_VERIFIED = "system_verified", "시스템 확인"

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="ownerships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="vehicle_ownerships")
    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True, blank=True)
    verification_method = models.CharField(max_length=32, default="account_registration")
    verification_status = models.CharField(max_length=24, choices=VerificationStatus.choices, default=VerificationStatus.USER_CLAIMED)

    class Meta:
        ordering = ["-started_at", "-id"]
        constraints = [models.UniqueConstraint(
            fields=["vehicle"],
            condition=models.Q(ended_at__isnull=True, user__isnull=False),
            name="one_active_vehicle_owner",
        )]

    def __str__(self):
        return f"{self.vehicle} · {self.user or '탈퇴 회원'}"

class VehicleTransferCode(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="transfer_codes")
    previous_owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="issued_vehicle_transfers")
    new_owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="accepted_vehicle_transfers")
    code_digest = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)
    invalidated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.vehicle} 인계 · {self.created_at:%Y-%m-%d}"

class LedgerEntry(models.Model):
    class Kind(models.TextChoices):
        FUEL = "fuel", "주유"
        SERVICE = "service", "정비"
        PART = "part", "소모품"
        WASH = "wash", "세차"
        OTHER = "other", "기타"
    class Source(models.TextChoices):
        OWNER = "owner", "차주 입력"
        PARTNER = "partner", "협력업체 인증"
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="ledger_entries")
    kind = models.CharField(max_length=16, choices=Kind.choices)
    entry_date = models.DateField(default=timezone.localdate)
    odometer_km = models.PositiveIntegerField(null=True, blank=True)
    amount_krw = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])
    description = models.CharField(max_length=160, blank=True)
    quantity_liters = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    source = models.CharField(max_length=16, choices=Source.choices, default=Source.OWNER)
    partner = models.ForeignKey("Partner", on_delete=models.PROTECT, related_name="verified_ledger_entries", null=True, blank=True)
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="verified_ledger_entries", null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    part_number = models.CharField(max_length=120, blank=True)
    evidence_url = models.URLField(blank=True)
    record_hash = models.CharField(max_length=64, blank=True, editable=False)
    corrects = models.ForeignKey("self", on_delete=models.PROTECT, related_name="corrections", null=True, blank=True)
    correction_reason = models.CharField(max_length=240, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-entry_date", "-id"]

class Reminder(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="reminders")
    title = models.CharField(max_length=100)
    due_date = models.DateField(null=True, blank=True)
    due_odometer_km = models.PositiveIntegerField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    notification_sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["due_date", "id"]

    @property
    def is_complete(self):
        return self.completed_at is not None

class PushDevice(models.Model):
    class Platform(models.TextChoices):
        ANDROID = "android", "Android"
        IOS = "ios", "iOS"
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="push_devices")
    installation_id = models.CharField(max_length=128, unique=True)
    platform = models.CharField(max_length=12, choices=Platform.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

class Notice(models.Model):
    title = models.CharField(max_length=140)
    summary = models.CharField(max_length=280, blank=True)
    body = models.TextField(blank=True)
    category = models.CharField(max_length=40, default="notice")
    original_url = models.URLField(blank=True)
    is_pinned = models.BooleanField(default=False)
    published_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_published = models.BooleanField(default=False)

    class Meta:
        ordering = ["-is_pinned", "-published_at"]


class AttendanceCheckin(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="attendance_checkins")
    checkin_date = models.DateField()
    points_awarded = models.PositiveIntegerField(default=1000)
    streak_days = models.PositiveSmallIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-checkin_date"]
        constraints = [models.UniqueConstraint(fields=["user", "checkin_date"], name="unique_user_daily_checkin")]

    def __str__(self):
        return f"{self.user_id} · {self.checkin_date} · {self.points_awarded}P"

class Partner(models.Model):
    name = models.CharField(max_length=120, unique=True)
    region = models.CharField(max_length=80, blank=True)
    service_categories = models.JSONField(default=list, blank=True)
    description = models.TextField(blank=True)
    address = models.CharField(max_length=240, blank=True)
    phone = models.CharField(max_length=40, blank=True)
    hours = models.CharField(max_length=160, blank=True)
    cafe_url = models.URLField(blank=True)
    map_url = models.URLField(blank=True)
    is_sponsored = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    display_order = models.PositiveSmallIntegerField(default=100)

    class Meta:
        ordering = ["display_order", "name"]

    def __str__(self):
        return self.name

class PartnerStaff(models.Model):
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name="staff_members")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="partner_memberships")
    can_verify_records = models.BooleanField(default=False)
    can_manage_bookings = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["partner", "user"], name="unique_partner_staff")]

    def __str__(self):
        return f"{self.partner} · {self.user}"


class PartnerBooking(models.Model):
    class Status(models.TextChoices):
        REQUESTED = "requested", "접수 대기"
        CONFIRMED = "confirmed", "예약 확정"
        REJECTED = "rejected", "예약 거절"
        CANCELLED = "cancelled", "취소"
        COMPLETED = "completed", "완료"

    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="partner_bookings")
    partner = models.ForeignKey(Partner, on_delete=models.PROTECT, related_name="bookings")
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True, related_name="bookings")
    requested_at = models.DateTimeField(default=timezone.now)
    scheduled_at = models.DateTimeField()
    service_type = models.CharField(max_length=100)
    customer_note = models.CharField(max_length=500, blank=True)
    contact_phone = models.CharField(max_length=24, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.REQUESTED)
    partner_note = models.CharField(max_length=500, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-requested_at"]
        indexes = [models.Index(fields=["partner", "scheduled_at", "status"], name="core_partne_partner_427ead_idx")]

    def __str__(self):
        return f"{self.partner} · {self.scheduled_at:%Y-%m-%d %H:%M} · {self.get_status_display()}"

class Offer(models.Model):
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name="offers")
    title = models.CharField(max_length=140)
    description = models.TextField(blank=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    redemption_instructions = models.CharField(max_length=240, blank=True)
    is_active = models.BooleanField(default=False)

    class Meta:
        ordering = ["-starts_at", "title"]

class NaverIdentity(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="naver_identity")
    subject = models.CharField(max_length=64, unique=True)
    nickname = models.CharField(max_length=80, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class NaverOAuthAttempt(models.Model):
    state_digest = models.CharField(max_length=64, unique=True)
    ticket_digest = models.CharField(max_length=64, unique=True, null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE)
    provider_subject = models.CharField(max_length=64, blank=True)
    nickname = models.CharField(max_length=80, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    consumed_at = models.DateTimeField(null=True, blank=True)

class MemberConsent(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="member_consent")
    terms_accepted_at = models.DateTimeField()
    privacy_accepted_at = models.DateTimeField()
    marketing_opt_in = models.BooleanField(default=False)
