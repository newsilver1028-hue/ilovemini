from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
import uuid

class SeasonBanner(models.Model):
    asset_key = models.CharField("내장 배너", max_length=40, blank=True, choices=[("mini-october", "MINI 10월 프로모션")])
    title = models.CharField("시즌 제목", max_length=140)
    subtitle = models.CharField("안내 문구", max_length=240, blank=True)
    image_url = models.URLField("배너 이미지 주소", max_length=2048, blank=True, help_text="공개 HTTPS 이미지 주소. 비워두면 선택한 내장 배너를 사용하며, 내장 배너도 없으면 브랜드 안내만 표시합니다.")
    image_data = models.BinaryField(null=True, blank=True, editable=False)
    image_content_type = models.CharField(max_length=32, blank=True, editable=False)
    is_active = models.BooleanField("노출 활성화", default=False)
    starts_at = models.DateTimeField("노출 시작", default=timezone.now)
    ends_at = models.DateTimeField("노출 종료", null=True, blank=True)
    duration_seconds = models.PositiveSmallIntegerField("표시 시간(초)", default=3)
    priority = models.PositiveSmallIntegerField("우선순위", default=100, help_text="낮은 숫자부터 표시합니다.")

    class Meta:
        verbose_name = "앱 시작 시즌 배너"
        verbose_name_plural = "앱 시작 시즌 배너"
        ordering = ["priority", "-starts_at", "-pk"]

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.ends_at and self.starts_at and self.ends_at <= self.starts_at:
            raise ValidationError({"ends_at": "종료는 시작보다 늦어야 합니다."})
        if not 1 <= self.duration_seconds <= 5:
            raise ValidationError({"duration_seconds": "1~5초로 설정해 주세요."})
        if self.image_url and not self.image_url.startswith("https://"):
            raise ValidationError({"image_url": "HTTPS 이미지 주소를 입력해 주세요."})

    def __str__(self):
        return self.title

class Vehicle(models.Model):
    nickname = models.CharField(max_length=40, blank=True)
    model_name = models.CharField(max_length=80)
    generation = models.CharField(max_length=40, blank=True)
    manufacturer = models.CharField(max_length=80, default="MINI")
    model_year = models.PositiveSmallIntegerField(null=True, blank=True)
    plate_number = models.CharField(max_length=16, blank=True, default="", db_index=True)
    first_registration_date = models.DateField(null=True, blank=True)
    vin_hash = models.CharField(max_length=64, blank=True, db_index=True)
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    passport_public = models.BooleanField(default=False)
    status = models.CharField(max_length=16, default="active")
    current_odometer_km = models.PositiveIntegerField(null=True, blank=True)
    retention_expires_at = models.DateTimeField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [models.UniqueConstraint(
            fields=["plate_number"],
            condition=models.Q(status="active") & ~models.Q(plate_number=""),
            name="uniq_active_vehicle_plate",
        )]

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
        USER_CLAIMED = "user_claimed", "사용자 등록·소유 미확인"
        DOCUMENT_VERIFIED = "document_verified", "서류 확인"
        SYSTEM_VERIFIED = "system_verified", "시스템 확인"

    class Relationship(models.TextChoices):
        OWNED = "owned", "자가 차량"
        LEASE = "lease", "리스 차량"
        RENTAL = "rental", "렌트 차량"
        FAMILY = "family", "가족 차량"
        OTHER = "other", "기타 이용 차량"

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="ownerships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="vehicle_ownerships")
    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True, blank=True)
    verification_method = models.CharField(max_length=32, default="account_registration")
    verification_status = models.CharField(max_length=24, choices=VerificationStatus.choices, default=VerificationStatus.USER_CLAIMED)
    relationship = models.CharField(max_length=16, choices=Relationship.choices, default=Relationship.OWNED)

    class Meta:
        ordering = ["-started_at", "-id"]
        constraints = [models.UniqueConstraint(
            fields=["vehicle"],
            condition=models.Q(ended_at__isnull=True, user__isnull=False),
            name="one_active_vehicle_owner",
        )]

    def __str__(self):
        return f"{self.vehicle} · {self.user or '탈퇴 회원'}"


class VehiclePlateHistory(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="plate_history")
    plate_number = models.CharField(max_length=16)
    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True, blank=True)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="vehicle_plate_changes")

    class Meta:
        ordering = ["-started_at", "-id"]
        constraints = [models.UniqueConstraint(
            fields=["plate_number"],
            condition=models.Q(ended_at__isnull=True),
            name="uniq_current_plate_history",
        )]

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
        SERVICE = "service", "정비·소모품"
        PART = "part", "정비·소모품"
        WASH = "wash", "세차"
        BODYWORK = "bodywork", "판금·도색·보험처리"
        WHEEL_TIRE = "wheel_tire", "휠·타이어"
        ELECTRICAL = "electrical", "전장류"
        OTHER = "other", "기타"
    class Source(models.TextChoices):
        OWNER = "owner", "차주 입력"
        PARTNER = "partner", "협력업체 인증"
    class PaymentMethod(models.TextChoices):
        CARD = "card", "카드"
        CASH = "cash", "현금"
        TRANSFER = "transfer", "계좌이체"
        EASY_PAY = "easy_pay", "간편결제"
        MIXED = "mixed", "복합결제"
        POINTS_ONLY = "points_only", "포인트 전액"
        OTHER = "other", "기타"
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="ledger_entries")
    kind = models.CharField(max_length=16, choices=Kind.choices)
    entry_date = models.DateField(default=timezone.localdate)
    odometer_km = models.PositiveIntegerField(null=True, blank=True)
    amount_krw = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])
    gross_amount_krw = models.PositiveIntegerField("정비 총액(포인트 차감 전, 원)", null=True, blank=True)
    payment_method = models.CharField("결제 수단", max_length=16, choices=PaymentMethod.choices, blank=True, default="")
    description = models.CharField(max_length=160, blank=True)
    line_items = models.JSONField("정비 항목별 금액", default=list, blank=True)
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


class LedgerEvidence(models.Model):
    entry = models.ForeignKey(LedgerEntry, on_delete=models.PROTECT, related_name="evidence_images")
    image_data = models.BinaryField(editable=False)
    content_type = models.CharField(max_