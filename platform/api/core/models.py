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
    content_type = models.CharField(max_length=32, editable=False)
    file_name = models.CharField(max_length=180, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "정비기록 첨부 사진"
        verbose_name_plural = "정비기록 첨부 사진"

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
    installation_id = models.CharField(max_length=2048, unique=True)
    platform = models.CharField(max_length=12, choices=Platform.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]


class WebPushSubscription(models.Model):
    """Browser push endpoint registered by an authorized partner staff member."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="web_push_subscriptions")
    partner = models.ForeignKey("Partner", on_delete=models.CASCADE, related_name="web_push_subscriptions")
    endpoint = models.URLField(max_length=2048)
    p256dh = models.CharField(max_length=256)
    auth = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "협력업체 PC 알림 구독"
        verbose_name_plural = "협력업체 PC 알림 구독"
        constraints = [models.UniqueConstraint(fields=["partner", "endpoint"], name="unique_partner_webpush_endpoint")]
        indexes = [models.Index(fields=["partner", "user"], name="core_webpush_partner_user_idx")]

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
    points_awarded = models.PositiveIntegerField(default=100)
    streak_days = models.PositiveSmallIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-checkin_date"]
        constraints = [models.UniqueConstraint(fields=["user", "checkin_date"], name="unique_user_daily_checkin")]

    def __str__(self):
        return f"{self.user_id} · {self.checkin_date} · {self.points_awarded}P"


class PointTransaction(models.Model):
    class Type(models.TextChoices):
        ATTENDANCE = "attendance", "출석 적립"
        SERVICE_EARN = "service_earn", "정비 결제 적립"
        REDEMPTION = "redemption", "포인트 사용"
        REFUND = "refund", "사용 취소·환급"
        ADJUSTMENT = "adjustment", "운영자 조정"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="회원", on_delete=models.PROTECT, related_name="point_transactions")
    partner = models.ForeignKey("Partner", verbose_name="협력업체", on_delete=models.PROTECT, null=True, blank=True, related_name="point_transactions")
    ledger_entry = models.ForeignKey("LedgerEntry", verbose_name="정비 기록", on_delete=models.PROTECT, null=True, blank=True, related_name="point_transactions")
    transaction_type = models.CharField("거래 종류", max_length=20, choices=Type.choices)
    points_delta = models.IntegerField("포인트 변동", help_text="적립은 양수, 사용은 음수로 기록합니다.")
    available_at = models.DateTimeField("사용 가능 시각", default=timezone.now)
    memo = models.CharField("처리 내용", max_length=240, blank=True)
    idempotency_key = models.CharField("중복 방지 키", max_length=100, unique=True, default=uuid.uuid4)
    created_at = models.DateTimeField("거래 시각", auto_now_add=True)

    class Meta:
        verbose_name = "포인트 거래 내역"
        verbose_name_plural = "포인트 거래 내역"
        ordering = ["-created_at", "-pk"]

    def __str__(self):
        sign = "+" if self.points_delta > 0 else ""
        return f"회원 {self.user_id} · {sign}{self.points_delta}P"


class PointRedemptionRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "승인 대기"
        APPROVED = "approved", "회원 승인"
        COMPLETED = "completed", "사용 완료"
        REJECTED = "rejected", "회원 거절"
        EXPIRED = "expired", "시간 만료"
        CANCELLED = "cancelled", "업체 취소"

    member = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="회원", on_delete=models.PROTECT, related_name="point_redemption_requests")
    partner = models.ForeignKey("Partner", verbose_name="협력업체", on_delete=models.PROTECT, related_name="point_redemption_requests")
    payment_amount_krw = models.PositiveIntegerField("결제 금액(원)")
    points_requested = models.PositiveIntegerField("사용 요청 포인트")
    status = models.CharField("처리 상태", max_length=16, choices=Status.choices, default=Status.PENDING)
    expires_at = models.DateTimeField("요청 만료 시각")
    responded_at = models.DateTimeField("회원 응답 시각", null=True, blank=True)
    completed_at = models.DateTimeField("사용 완료 시각", null=True, blank=True)
    transaction = models.ForeignKey(PointTransaction, verbose_name="포인트 거래", on_delete=models.PROTECT, null=True, blank=True, related_name="redemption_requests")
    created_at = models.DateTimeField("요청 시각", auto_now_add=True)

    class Meta:
        verbose_name = "포인트 사용 승인 요청"
        verbose_name_plural = "포인트 사용 승인 요청"
        ordering = ["-created_at", "-pk"]

    def __str__(self):
        return f"{self.partner} · 회원 {self.member_id} · {self.points_requested}P"

class Partner(models.Model):
    name = models.CharField(max_length=120)
    branch_label = models.CharField(max_length=80, blank=True, default="")
    region = models.CharField(max_length=80, blank=True)
    service_categories = models.JSONField(default=list, blank=True)
    description = models.TextField(blank=True)
    address = models.CharField(max_length=240, blank=True)
    phone = models.CharField(max_length=40, blank=True)
    hours = models.CharField(max_length=160, blank=True)
    cafe_url = models.URLField(blank=True)
    kakao_channel_url = models.URLField("카카오톡 채널 상담 주소", max_length=2048, blank=True, help_text="예: https://pf.kakao.com/_채널ID/chat")
    map_url = models.URLField(blank=True)
    storefront_photo_url = models.URLField(max_length=2048, blank=True)
    storefront_photo_data = models.BinaryField(null=True, blank=True, editable=False)
    storefront_photo_content_type = models.CharField(max_length=32, blank=True, editable=False)
    business_info = models.TextField(blank=True)
    representative_name = models.CharField(max_length=100, blank=True)
    representative_title = models.CharField(max_length=100, blank=True)
    representative_experience_years = models.PositiveSmallIntegerField(null=True, blank=True)
    representative_photo_url = models.URLField(max_length=2048, blank=True)
    representative_photo_data = models.BinaryField(null=True, blank=True, editable=False)
    representative_photo_content_type = models.CharField(max_length=32, blank=True, editable=False)
    is_sponsored = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    display_order = models.PositiveSmallIntegerField(default=100)

    class Meta:
        ordering = ["display_order", "name"]
        constraints = [models.UniqueConstraint(fields=["name", "branch_label"], name="unique_partner_name_branch")]

    def __str__(self):
        return f"{self.name} · {self.branch_label}" if self.branch_label else self.name


class PartnerQuoteShare(models.Model):
    """Short-lived, opaque customer link for a partner quote document."""
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    work_order = models.ForeignKey("PartnerWorkOrder", null=True, blank=True, on_delete=models.CASCADE, related_name="quote_shares")
    estimate = models.ForeignKey("ServiceEstimate", null=True, blank=True, on_delete=models.CASCADE, related_name="quote_shares")
    quote_revision = models.PositiveSmallIntegerField("견적 버전", default=0)
    snapshot = models.JSONField("공유 당시 견적 내용", default=dict, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(db_index=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [models.CheckConstraint(
            condition=(models.Q(work_order__isnull=False, estimate__isnull=True) | models.Q(work_order__isnull=True, estimate__isnull=False)),
            name="partner_quote_share_exactly_one_source",
        )]

    def __str__(self):
        return f"견적 공유 · {self.token}"


class PartnerServiceCategoryOption(models.Model):
    name = models.CharField("서비스 분야", max_length=80, unique=True)
    is_active = models.BooleanField("사용", default=True)
    display_order = models.PositiveSmallIntegerField("표시 순서", default=100)

    class Meta:
        ordering = ["display_order", "name"]
        verbose_name = "업체 서비스 분야"
        verbose_name_plural = "업체 서비스 분야"

    def __str__(self):
        return self.name


class PartnerImage(models.Model):
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name="introduction_images")
    caption = models.CharField("이미지 설명", max_length=160, blank=True)
    image_data = models.BinaryField(editable=False)
    content_type = models.CharField(max_length=32, editable=False)
    display_order = models.PositiveSmallIntegerField("표시 순서", default=0)

    class Meta:
        ordering = ["display_order", "pk"]
        verbose_name = "업체 소개 이미지"
        verbose_name_plural = "업체 소개 이미지"

    def __str__(self):
        return self.caption or f"{self.partner} 소개 이미지"


class PartnerReview(models.Model):
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="partner_reviews")
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.CharField(max_length=1000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [models.UniqueConstraint(fields=["partner", "user"], name="unique_partner_review_user")]

    def __str__(self):
        return f"{self.partner} · {self.rating}/5"

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


class PartnerAccessRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "승인 대기"
        APPROVED = "approved", "승인"
        REJECTED = "rejected", "반려"

    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name="access_requests", verbose_name="신청 업체")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="partner_access_requests", verbose_name="네이버 계정")
    status = models.CharField("처리 상태", max_length=12, choices=Status.choices, default=Status.PENDING)
    can_verify_records = models.BooleanField("정비기록 인증 권한", default=False)
    can_manage_bookings = models.BooleanField("예약 관리 권한", default=False)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="reviewed_partner_access_requests", verbose_name="처리 관리자")
    reviewed_at = models.DateTimeField("처리 일시", null=True, blank=True)
    created_at = models.DateTimeField("신청 일시", auto_now_add=True)
    updated_at = models.DateTimeField("수정 일시", auto_now=True)

    class Meta:
        ordering = ["status", "-created_at", "-id"]
        verbose_name = "협력업체 권한 신청"
        verbose_name_plural = "협력업체 권한 신청"
        constraints = [models.UniqueConstraint(fields=["partner", "user"], name="unique_partner_access_request")]

    def __str__(self):
        return f"{self.partner} · {self.user} · {self.get_status_display()}"


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
    duration_minutes = models.PositiveSmallIntegerField("예상 작업 시간(분)", default=60, help_text="30분 단위. 기존 예약의 작업 시간은 저장 당시 값으로 유지됩니다.")
    assigned_resource = models.ForeignKey("PartnerWorkResource", on_delete=models.SET_NULL, null=True, blank=True, related_name="bookings", verbose_name="담당 정비사·작업대")
    service_type = models.CharField(max_length=100)
    customer_note = models.CharField(max_length=500, blank=True)
    contact_phone = models.CharField(max_length=24, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.REQUESTED)
    cancellation_reason = models.CharField("예약 취소 사유", max_length=500, blank=True, default="")
    partner_note = models.CharField(max_length=500, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-requested_at"]
        verbose_name = "업체 예약"
        verbose_name_plural = "업체 예약"
        indexes = [models.Index(fields=["partner", "scheduled_at", "status"], name="core_partne_partner_427ead_idx")]

    def __str__(self):
        scheduled_at = timezone.localtime(self.scheduled_at)
        return f"{self.partner} · {scheduled_at:%Y-%m-%d %H:%M} · {self.get_status_display()}"


class PartnerServiceDuration(models.Model):
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name="booking_service_durations")
    service_name = models.CharField("정비 항목", max_length=100)
    duration_minutes = models.PositiveSmallIntegerField("기본 작업 시간(분)", default=60, help_text="30분 단위, 30~480분")
    is_active = models.BooleanField("예약 가능", default=True)

    class Meta:
        verbose_name = "예약 정비 시간"
        verbose_name_plural = "예약 정비 시간"
        ordering = ["partner", "service_name"]
        constraints = [models.UniqueConstraint(fields=["partner", "service_name"], name="unique_partner_booking_service")]

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.duration_minutes < 30 or self.duration_minutes > 480 or self.duration_minutes % 30:
            raise ValidationError({"duration_minutes": "작업 시간은 30분 단위로 30~480분 사이에서 설정해 주세요."})

    def __str__(self):
        return f"{self.partner} · {self.service_name} ({self.duration_minutes}분)"


class PartnerWeeklySchedule(models.Model):
    WEEKDAYS = [(0, "월요일"), (1, "화요일"), (2, "수요일"), (3, "목요일"), (4, "금요일"), (5, "토요일"), (6, "일요일")]
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name="weekly_booking_schedule")
    weekday = models.PositiveSmallIntegerField("요일", choices=WEEKDAYS)
    opens_at = models.TimeField("예약 시작", null=True, blank=True)
    closes_at = models.TimeField("마감", null=True, blank=True)
    is_closed = models.BooleanField("휴무", default=False)
    slot_interval_minutes = models.PositiveSmallIntegerField("예약 시작 간격(분)", default=30)

    class Meta:
        verbose_name = "주간 예약 운영시간"
        verbose_name_plural = "주간 예약 운영시간"
        ordering = ["partner", "weekday"]
        constraints = [models.UniqueConstraint(fields=["partner", "weekday"], name="unique_partner_booking_weekday")]

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.slot_interval_minutes not in (30, 60):
            raise ValidationError({"slot_interval_minutes": "예약 시작 간격은 30분 또는 60분으로 설정해 주세요."})
        if not self.is_closed and (not self.opens_at or not self.closes_at or self.opens_at >= self.closes_at):
            raise ValidationError({"closes_at": "운영일에는 예약 시작과 마감 시간을 입력하고, 마감은 시작보다 늦게 설정해 주세요."})

    def __str__(self):
        label = dict(self.WEEKDAYS).get(self.weekday, "요일")
        return f"{self.partner} · {label} · {'휴무' if self.is_closed else f'{self.opens_at:%H:%M}–{self.closes_at:%H:%M}'}"


class PartnerScheduleException(models.Model):
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name="booking_schedule_exceptions")
    date = models.DateField("적용 날짜")
    is_closed = models.BooleanField("종일 휴무", default=False)
    opens_at = models.TimeField("해당일 예약 시작", null=True, blank=True)
    closes_at = models.TimeField("해당일 마감", null=True, blank=True)
    note = models.CharField("메모", max_length=160, blank=True)

    class Meta:
        verbose_name = "날짜별 예약 일정 변경"
        verbose_name_plural = "날짜별 예약 일정 변경"
        ordering = ["date", "partner"]
        constraints = [models.UniqueConstraint(fields=["partner", "date"], name="unique_partner_booking_exception")]

    def clean(self):
        from django.core.exceptions import ValidationError
        if not self.is_closed and (not self.opens_at or not self.closes_at or self.opens_at >= self.closes_at):
            raise ValidationError("휴무가 아니면 예약 시작과 마감 시간을 올바르게 입력해 주세요.")

    def __str__(self):
        return f"{self.partner} · {self.date} · {'휴무' if self.is_closed else '운영시간 변경'}"


class PartnerScheduleBlock(models.Model):
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name="booking_schedule_blocks")
    starts_at = models.DateTimeField("차단 시작")
    ends_at = models.DateTimeField("차단 종료")
    reason = models.CharField("사유", max_length=160, blank=True)

    class Meta:
        verbose_name = "예약 시간 차단"
        verbose_name_plural = "예약 시간 차단"
        ordering = ["starts_at"]

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.ends_at <= self.starts_at:
            raise ValidationError({"ends_at": "차단 종료는 시작보다 늦어야 합니다."})

    def __str__(self):
        return f"{self.partner} · {self.starts_at:%Y-%m-%d %H:%M}–{self.ends_at:%H:%M}"


class PartnerWorkOrder(models.Model):
    """Partner-scoped repair intake and workshop job card."""

    class Status(models.TextChoices):
        RECEIVED = "received", "접수"
        INSPECTING = "inspecting", "점검 중"
        QUOTE = "quote", "견적 작성"
        WAITING_APPROVAL = "waiting_approval", "고객 승인 대기"
        WAITING_PARTS = "waiting_parts", "부품 대기"
        IN_PROGRESS = "in_progress", "정비 중"
        READY = "ready", "출고 대기"
        COMPLETED = "completed", "정비 완료"
        CANCELLED = "cancelled", "취소"

    class PaymentMethod(models.TextChoices):
        CARD = "card", "카드"
        CASH = "cash", "현금"
        TRANSFER = "transfer", "계좌이체"
        EASY_PAY = "easy_pay", "간편결제"
        OTHER = "other", "기타"

    class QuoteStatus(models.TextChoices):
        DRAFT = "draft", "미발송"
        SENT = "sent", "고객 확인 대기"
        APPROVED = "approved", "고객 승인"
        DECLINED = "declined", "고객 거절"

    partner = models.ForeignKey(Partner, on_delete=models.PROTECT, related_name="work_orders", verbose_name="협력업체")
    booking = models.OneToOneField(PartnerBooking, on_delete=models.PROTECT, null=True, blank=True, related_name="work_order", verbose_name="연결 예약")
    customer = models.ForeignKey("PartnerCustomer", on_delete=models.SET_NULL, null=True, blank=True, related_name="work_orders", verbose_name="등록 고객")
    partner_vehicle = models.ForeignKey("PartnerVehicle", on_delete=models.SET_NULL, null=True, blank=True, related_name="work_orders", verbose_name="업체 차량대장")
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True, related_name="partner_work_orders", verbose_name="등록 차량")
    customer_name = models.CharField("고객명", max_length=100, blank=True)
    contact_phone = models.CharField("연락처", max_length=24, blank=True)
    vehicle_model = models.CharField("차량명", max_length=100, blank=True)
    plate_number = models.CharField("차량번호", max_length=16, blank=True, db_index=True)
    odometer_km = models.PositiveIntegerField("입고 주행거리(km)", null=True, blank=True)
    customer_concern = models.TextField("고객 요청·증상", blank=True)
    inspection_notes = models.TextField("점검·진단 내용", blank=True)
    work_notes = models.TextField("작업 내용", blank=True)
    customer_message = models.CharField("고객 안내", max_length=500, blank=True)
    technician_name = models.CharField("담당 정비사", max_length=100, blank=True)
    assigned_resource = models.ForeignKey("PartnerWorkResource", on_delete=models.SET_NULL, null=True, blank=True, related_name="work_orders", verbose_name="담당 정비사·작업대")
    items = models.JSONField("부품·공임 항목", default=list, blank=True)
    quoted_total_krw = models.PositiveIntegerField("견적 금액(원)", default=0)
    quote_status = models.CharField("견적 확인 상태", max_length=12, choices=QuoteStatus.choices, default=QuoteStatus.DRAFT)
    quote_revision = models.PositiveSmallIntegerField("견적 버전", default=0)
    quote_responded_at = models.DateTimeField("고객 응답 시각", null=True, blank=True)
    quote_decline_reason = models.CharField("고객 거절 사유", max_length=500, blank=True)
    final_total_krw = models.PositiveIntegerField("최종 정비 금액(원)", default=0)
    paid_amount_krw = models.PositiveIntegerField("수납 금액(원)", default=0)
    payment_method = models.CharField("결제 수단", max_length=16, choices=PaymentMethod.choices, blank=True)
    status = models.CharField("작업 상태", max_length=24, choices=Status.choices, default=Status.RECEIVED)
    internal_note = models.TextField("업체 내부 메모", blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="partner_work_orders_created", verbose_name="접수 담당자")
    created_at = models.DateTimeField("접수 시각", auto_now_add=True)
    updated_at = models.DateTimeField("수정 시각", auto_now=True)
    completed_at = models.DateTimeField("완료 시각", null=True, blank=True)

    class Meta:
        verbose_name = "정비 접수·작업지시"
        verbose_name_plural = "정비 접수·작업지시"
        ordering = ["-created_at", "-pk"]
        indexes = [models.Index(fields=["partner", "status", "created_at"], name="partner_work_status_idx")]

    def __str__(self):
        return f"작업 #{self.pk or '신규'} · {self.plate_number or self.vehicle_model or self.customer_name or '차량 미지정'}"


class PartnerCustomer(models.Model):
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name="workshop_customers", verbose_name="협력업체")
    name = models.CharField("고객명", max_length=100)
    phone = models.CharField("연락처", max_length=24, db_index=True)
    email = models.EmailField("이메일", blank=True)
    address = models.CharField("주소", max_length=240, blank=True)
    business_number = models.CharField("사업자등록번호", max_length=20, blank=True)
    notes = models.TextField("고객 메모", blank=True)
    is_active = models.BooleanField("관리 중", default=True)
    created_at = models.DateTimeField("등록일", auto_now_add=True)
    updated_at = models.DateTimeField("수정일", auto_now=True)

    class Meta:
        verbose_name = "고객 대장"
        verbose_name_plural = "고객 대장"
        ordering = ["name", "pk"]
        indexes = [models.Index(fields=["partner", "phone"], name="partner_customer_phone_idx")]

    def __str__(self):
        return f"{self.name} · {self.phone}"


class PartnerVehicle(models.Model):
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name="workshop_vehicles", verbose_name="협력업체")
    customer = models.ForeignKey(PartnerCustomer, on_delete=models.CASCADE, related_name="vehicles", verbose_name="고객")
    plate_number = models.CharField("차량번호", max_length=16, db_index=True)
    manufacturer = models.CharField("제조사", max_length=80, blank=True)
    model_name = models.CharField("차종", max_length=100)
    model_year = models.PositiveSmallIntegerField("연식", null=True, blank=True)
    vin = models.CharField("차대번호", max_length=32, blank=True)
    first_registration_date = models.DateField("최초 등록일", null=True, blank=True)
    current_odometer_km = models.PositiveIntegerField("현재 주행거리(km)", null=True, blank=True)
    notes = models.TextField("차량 메모", blank=True)
    is_active = models.BooleanField("관리 중", default=True)

    class Meta:
        verbose_name = "업체 차량 대장"
        verbose_name_plural = "업체 차량 대장"
        ordering = ["plate_number", "pk"]
        constraints = [models.UniqueConstraint(fields=["partner", "plate_number"], name="unique_partner_vehicle_plate")]

    def __str__(self):
        return f"{self.plate_number} · {self.model_name}"


class PartnerWorkOrderLine(models.Model):
    class Kind(models.TextChoices):
        PART = "part", "부품"
        LABOR = "labor", "공임"
        OUTSOURCE = "outsource", "외주"
        OTHER = "other", "기타"

    work_order = models.ForeignKey(PartnerWorkOrder, on_delete=models.CASCADE, related_name="lines", verbose_name="작업지시")
    preset = models.ForeignKey("PartnerServicePreset", on_delete=models.SET_NULL, null=True, blank=True, related_name="work_order_lines", verbose_name="표준 정비 항목")
    kind = models.CharField("유형", max_length=12, choices=Kind.choices, default=Kind.LABOR)
    part = models.ForeignKey("PartnerPart", null=True, blank=True, on_delete=models.PROTECT, related_name="work_order_lines", verbose_name="재고 부품")
    description = models.CharField("작업·부품명", max_length=160)
    quantity = models.DecimalField("수량", max_digits=9, decimal_places=2, default=1, validators=[MinValueValidator(0.01)])
    unit = models.CharField("단위", max_length=24, blank=True)
    unit_price_krw = models.PositiveIntegerField("단가(원)", default=0)
    sort_order = models.PositiveSmallIntegerField("순서", default=0)

    class Meta:
        verbose_name = "정비 항목"
        verbose_name_plural = "정비 항목"
        ordering = ["sort_order", "pk"]

    @property
    def amount_krw(self):
        return int(self.quantity * self.unit_price_krw)

    def __str__(self):
        return self.description


class PartnerWorkResource(models.Model):
    class Kind(models.TextChoices):
        TECHNICIAN = "technician", "정비사"
        BAY = "bay", "작업대·리프트"

    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name="work_resources", verbose_name="협력업체")
    name = models.CharField("이름·작업대", max_length=100)
    kind = models.CharField("구분", max_length=16, choices=Kind.choices, default=Kind.TECHNICIAN)
    is_active = models.BooleanField("사용", default=True)

    class Meta:
        verbose_name = "정비사·작업대"
        verbose_name_plural = "정비사·작업대"
        ordering = ["partner", "kind", "name"]
        constraints = [models.UniqueConstraint(fields=["partner", "kind", "name"], name="unique_partner_work_resource")]

    def __str__(self):
        return f"{self.get_kind_display()} · {self.name}"


class PartnerServicePreset(models.Model):
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name="service_presets", verbose_name="협력업체")
    name = models.CharField("정비 항목", max_length=160)
    kind = models.CharField("유형", max_length=12, choices=PartnerWorkOrderLine.Kind.choices, default=PartnerWorkOrderLine.Kind.LABOR)
    duration_minutes = models.PositiveSmallIntegerField("예상 소요시간(분)", default=60)
    default_quantity = models.DecimalField("기본 수량", max_digits=9, decimal_places=2, default=1)
    unit = models.CharField("단위", max_length=24, blank=True)
    default_price_krw = models.PositiveIntegerField("기본 단가(원)", default=0)
    part = models.ForeignKey("PartnerPart", on_delete=models.SET_NULL, null=True, blank=True, related_name="service_presets", verbose_name="연결 재고 부품")
    is_active = models.BooleanField("사용", default=True)

    class Meta:
        verbose_name = "표준 정비 항목·공임"
        verbose_name_plural = "표준 정비 항목·공임"
        ordering = ["partner", "name"]
        constraints = [models.UniqueConstraint(fields=["partner", "name"], name="unique_partner_service_preset")]

    def __str__(self):
        return self.name


class PartnerDailyClose(models.Model):
    partner = models.ForeignKey(Partner, on_delete=models.PROTECT, related_name="daily_closes", verbose_name="협력업체")
    business_date = models.DateField("영업일")
    expected_cash_krw = models.PositiveIntegerField("시스템 현금 합계(원)", default=0)
    counted_cash_krw = models.PositiveIntegerField("실제 현금(원)", default=0)
    expected_card_krw = models.PositiveIntegerField("시스템 카드 합계(원)", default=0)
    counted_card_krw = models.PositiveIntegerField("실제 카드 정산액(원)", default=0)
    expected_transfer_krw = models.PositiveIntegerField("시스템 이체 합계(원)", default=0)
    counted_transfer_krw = models.PositiveIntegerField("실제 이체 합계(원)", default=0)
    expected_refund_krw = models.PositiveIntegerField("시스템 환불 합계(원)", default=0)
    counted_refund_krw = models.PositiveIntegerField("실제 환불 합계(원)", default=0)
    note = models.CharField("마감 메모", max_length=500, blank=True)
    closed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="partner_daily_closes")
    closed_at = models.DateTimeField("마감 시각", auto_now_add=True)

    class Meta:
        verbose_name = "일일 매출 마감"
        verbose_name_plural = "일일 매출 마감"
        ordering = ["-business_date", "partner"]
        constraints = [models.UniqueConstraint(fields=["partner", "business_date"], name="unique_partner_daily_close")]

    def __str__(self):
        return f"{self.partner} · {self.business_date} 마감"


class PartnerSupplier(models.Model):
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name="suppliers", verbose_name="협력업체")
    name = models.CharField("거래처명", max_length=120)
    contact_name = models.CharField("담당자", max_length=80, blank=True)
    phone = models.CharField("전화번호", max_length=32, blank=True)
    email = models.EmailField("이메일", blank=True)
    address = models.CharField("주소", max_length=240, blank=True)
    business_number = models.CharField("사업자등록번호", max_length=20, blank=True)
    note = models.TextField("메모", blank=True)
    is_active = models.BooleanField("거래 중", default=True)

    class Meta:
        verbose_name = "부품 거래처"
        verbose_name_plural = "부품 거래처"
        ordering = ["name", "pk"]
        constraints = [models.UniqueConstraint(fields=["partner", "name"], name="unique_partner_supplier_name")]

    def __str__(self):
        return self.name


class PartnerPart(models.Model):
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name="parts", verbose_name="협력업체")
    sku = models.CharField("관리번호", max_length=64, blank=True)
    part_number = models.CharField("부품번호", max_length=100, blank=True)
    name = models.CharField("부품명", max_length=160)
    maker = models.CharField("제조사", max_length=100, blank=True)
    unit = models.CharField("단위", max_length=24, default="개")
    location = models.CharField("적재 위치", max_length=80, blank=True)
    purchase_price_krw = models.PositiveIntegerField("매입 단가(원)", default=0)
    sale_price_krw = models.PositiveIntegerField("판매 단가(원)", default=0)
    stock_quantity = models.PositiveIntegerField("현재고", default=0)
    reorder_level = models.PositiveIntegerField("재주문 기준", default=0)
    is_active = models.BooleanField("사용", default=True)
    updated_at = models.DateTimeField("수정일", auto_now=True)

    class Meta:
        verbose_name = "부품 정보"
        verbose_name_plural = "부품 정보"
        ordering = ["name", "pk"]
        constraints = [models.UniqueConstraint(fields=["partner", "sku"], condition=~models.Q(sku=""), name="unique_partner_part_sku")]
        indexes = [models.Index(fields=["partner", "name"], name="partner_part_name_idx")]

    def __str__(self):
        return f"{self.name} · {self.sku}" if self.sku else self.name


class PartnerPurchaseLine(models.Model):
    partner = models.ForeignKey(Partner, on_delete=models.PROTECT, related_name="purchase_lines", verbose_name="협력업체")
    supplier = models.ForeignKey(PartnerSupplier, on_delete=models.PROTECT, related_name="purchase_lines", verbose_name="매입처")
    part = models.ForeignKey(PartnerPart, on_delete=models.PROTECT, related_name="purchase_lines", verbose_name="부품")
    invoice_number = models.CharField("전표 번호", max_length=80, blank=True)
    purchased_at = models.DateField("매입일", default=timezone.localdate)
    quantity = models.PositiveIntegerField("수량", validators=[MinValueValidator(1)])
    unit_price_krw = models.PositiveIntegerField("매입 단가(원)")
    total_krw = models.PositiveIntegerField("매입 합계(원)", default=0)
    paid_krw = models.PositiveIntegerField("지불액(원)", default=0)
    note = models.CharField("메모", max_length=240, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="partner_purchases_created")
    created_at = models.DateTimeField("등록일", auto_now_add=True)

    class Meta:
        verbose_name = "부품 매입 등록"
        verbose_name_plural = "부품 매입 등록"
        ordering = ["-purchased_at", "-pk"]

    def __str__(self):
        return f"{self.part.name} · {self.purchased_at} · {self.total_krw:,}원"


class PartnerStockMovement(models.Model):
    class Direction(models.TextChoices):
        IN = "in", "입고"
        OUT = "out", "출고"

    class Reason(models.TextChoices):
        PURCHASE = "purchase", "부품 매입"
        REPAIR_USE = "repair_use", "정비 사용"
        ADJUSTMENT = "adjustment", "재고 조정"
        RETURN = "return", "반품"
        DAMAGE = "damage", "파손·폐기"
        OTHER = "other", "기타"

    partner = models.ForeignKey(Partner, on_delete=models.PROTECT, related_name="stock_movements", verbose_name="협력업체")
    part = models.ForeignKey(PartnerPart, on_delete=models.PROTECT, related_name="movements", verbose_name="부품")
    purchase = models.ForeignKey(PartnerPurchaseLine, null=True, blank=True, on_delete=models.PROTECT, related_name="stock_movements")
    work_order = models.ForeignKey(PartnerWorkOrder, null=True, blank=True, on_delete=models.PROTECT, related_name="stock_movements", verbose_name="연결 작업")
    direction = models.CharField("구분", max_length=8, choices=Direction.choices)
    reason = models.CharField("사유", max_length=16, choices=Reason.choices, default=Reason.ADJUSTMENT)
    quantity = models.PositiveIntegerField("수량", validators=[MinValueValidator(1)])
    balance_after = models.PositiveIntegerField("처리 후 재고", default=0)
    note = models.CharField("메모", max_length=240, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="partner_stock_movements_created")
    created_at = models.DateTimeField("처리일", auto_now_add=True)

    class Meta:
        verbose_name = "재고 입출고 기록"
        verbose_name_plural = "재고 입출고 기록"
        ordering = ["-created_at", "-pk"]

    def __str__(self):
        return f"{self.part.name} · {self.get_direction_display()} {self.quantity}"


class PartnerFinancialEntry(models.Model):
    class Kind(models.TextChoices):
        INCOME = "income", "입금"
        EXPENSE = "expense", "경비"

    class Method(models.TextChoices):
        CASH = "cash", "현금"
        CARD = "card", "카드"
        TRANSFER = "transfer", "계좌이체"
        OTHER = "other", "기타"

    partner = models.ForeignKey(Partner, on_delete=models.PROTECT, related_name="financial_entries", verbose_name="협력업체")
    kind = models.CharField("구분", max_length=12, choices=Kind.choices)
    category = models.CharField("항목", max_length=100)
    occurred_at = models.DateField("처리일", default=timezone.localdate)
    amount_krw = models.PositiveIntegerField("금액(원)", validators=[MinValueValidator(1)])
    payment_method = models.CharField("결제 수단", max_length=12, choices=Method.choices, blank=True)
    counterparty = models.CharField("상대방", max_length=100, blank=True)
    work_order = models.ForeignKey(PartnerWorkOrder, null=True, blank=True, on_delete=models.PROTECT, related_name="financial_entries", verbose_name="연결 작업")
    note = models.CharField("메모", max_length=240, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="partner_financial_entries_created")
    created_at = models.DateTimeField("등록일", auto_now_add=True)

    class Meta:
        verbose_name = "입금·경비 기록"
        verbose_name_plural = "입금·경비 기록"
        ordering = ["-occurred_at", "-pk"]
        indexes = [models.Index(fields=["partner", "occurred_at", "kind"], name="partner_finance_day_idx")]

    def __str__(self):
        return f"{self.get_kind_display()} · {self.category} · {self.amount_krw:,}원"


class PartnerPosIntegration(models.Model):
    """Per-shop receiver for normalized POS payment events."""

    partner = models.OneToOneField(Partner, on_delete=models.CASCADE, related_name="pos_integration", verbose_name="협력업체")
    provider_name = models.CharField("POS/VAN 제공사", max_length=80, blank=True)
    token_hash = models.CharField("Webhook 토큰 해시", max_length=64, blank=True, editable=False)
    is_active = models.BooleanField("연동 사용", default=False)
    last_received_at = models.DateTimeField("마지막 수신", null=True, blank=True)
    created_at = models.DateTimeField("등록일", auto_now_add=True)
    updated_at = models.DateTimeField("수정일", auto_now=True)

    class Meta:
        verbose_name = "POS 연동"
        verbose_name_plural = "POS 연동"

    def __str__(self):
        return f"{self.partner} · {self.provider_name or 'POS'}"


class PartnerPayment(models.Model):
    class Method(models.TextChoices):
        CARD = "card", "카드"
        CASH = "cash", "현금"
        TRANSFER = "transfer", "계좌이체"
        EASY_PAY = "easy_pay", "간편결제"
        OTHER = "other", "기타"

    class Status(models.TextChoices):
        APPROVED = "approved", "승인"
        CANCELLED = "cancelled", "취소"

    partner = models.ForeignKey(Partner, on_delete=models.PROTECT, related_name="payments", verbose_name="협력업체")
    work_order = models.ForeignKey(PartnerWorkOrder, on_delete=models.PROTECT, related_name="payments", verbose_name="정비 작업")
    provider_name = models.CharField("POS/VAN 제공사", max_length=80, default="POS")
    provider_transaction_id = models.CharField("거래 번호", max_length=120)
    method = models.CharField("결제 수단", max_length=16, choices=Method.choices)
    status = models.CharField("상태", max_length=12, choices=Status.choices, default=Status.APPROVED)
    amount_krw = models.PositiveIntegerField("결제 금액(원)")
    approval_code = models.CharField("승인 번호", max_length=80, blank=True)
    paid_at = models.DateTimeField("결제 일시", default=timezone.now)
    cancelled_at = models.DateTimeField("취소 처리 일시", null=True, blank=True)
    cancelled_amount_krw = models.PositiveIntegerField("취소 금액(원)", default=0)
    created_at = models.DateTimeField("수신 일시", auto_now_add=True)

    class Meta:
        verbose_name = "POS 결제 내역"
        verbose_name_plural = "POS 결제 내역"
        ordering = ["-paid_at", "-pk"]
        constraints = [models.UniqueConstraint(fields=["partner", "provider_name", "provider_transaction_id"], name="unique_partner_pos_transaction")]
        indexes = [models.Index(fields=["partner", "paid_at"], name="partner_payment_day_idx")]

    def __str__(self):
        return f"{self.work_order} · {self.amount_krw:,}원 · {self.get_status_display()}"


class PartnerTaxInvoice(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "발행 준비"
        ISSUED = "issued", "외부 발행 확인"
        CANCELLED = "cancelled", "취소"

    class TaxType(models.TextChoices):
        TAXABLE = "taxable", "과세"
        EXEMPT = "exempt", "면세"
        ZERO = "zero", "영세"

    class Purpose(models.TextChoices):
        BILL = "bill", "청구"
        RECEIPT = "receipt", "영수"

    partner = models.ForeignKey(Partner, on_delete=models.PROTECT, related_name="tax_invoices", verbose_name="협력업체")
    work_order = models.ForeignKey(PartnerWorkOrder, on_delete=models.PROTECT, related_name="tax_invoices", verbose_name="정비 작업")
    status = models.CharField("상태", max_length=12, choices=Status.choices, default=Status.DRAFT)
    tax_type = models.CharField("과세 유형", max_length=12, choices=TaxType.choices, default=TaxType.TAXABLE)
    purpose = models.CharField("발행 목적", max_length=12, choices=Purpose.choices, default=Purpose.RECEIPT)
    write_date = models.DateField("작성일", default=timezone.localdate)
    seller_business_number = models.CharField("공급자 사업자번호", max_length=20, blank=True)
    seller_name = models.CharField("공급자 상호", max_length=120, blank=True)
    seller_representative = models.CharField("공급자 대표자", max_length=100, blank=True)
    seller_address = models.CharField("공급자 주소", max_length=240, blank=True)
    seller_email = models.EmailField("공급자 이메일", blank=True)
    buyer_business_number = models.CharField("공급받는자 사업자번호", max_length=20)
    buyer_name = models.CharField("공급받는자 상호", max_length=120)
    buyer_representative = models.CharField("공급받는자 대표자", max_length=100, blank=True)
    buyer_address = models.CharField("공급받는자 주소", max_length=240, blank=True)
    buyer_email = models.EmailField("공급받는자 이메일", blank=True)
    supply_cost_krw = models.PositiveIntegerField("공급가액(원)")
    tax_krw = models.PositiveIntegerField("세액(원)")
    total_krw = models.PositiveIntegerField("합계(원)")
    items = models.JSONField("품목", default=list, blank=True)
    provider_name = models.CharField("발행 대행사", max_length=80, blank=True)
    provider_user_id = models.CharField("팝빌 사용자 ID", max_length=80, blank=True)
    provider_document_id = models.CharField("대행사 문서번호", max_length=120, blank=True)
    provider_error_code = models.CharField("최근 발행 오류 코드", max_length=40, blank=True)
    issued_at = models.DateTimeField("외부 발행 확인일", null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="partner_tax_invoices_created")
    created_at = models.DateTimeField("등록일", auto_now_add=True)

    class Meta:
        verbose_name = "전자세금계산서 발행 준비"
        verbose_name_plural = "전자세금계산서 발행 준비"
        ordering = ["-write_date", "-pk"]

    def __str__(self):
        return f"{self.buyer_name} · {self.total_krw:,}원 · {self.get_status_display()}"

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
    cafe_nickname = models.CharField("네이버 카페 닉네임", max_length=40, blank=True)
    name = models.CharField("회원 이름", max_length=150, blank=True)
    email = models.EmailField("연락처 이메일 주소", blank=True)
    profile_image = models.URLField("프로필 사진", max_length=2048, blank=True)
    gender = models.CharField("성별", max_length=16, blank=True)
    birthday = models.CharField("생일", max_length=16, blank=True)
    age = models.CharField("연령대", max_length=32, blank=True)
    birthyear = models.CharField("출생연도", max_length=8, blank=True)
    mobile = models.CharField("휴대전화번호", max_length=32, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class AppleIdentity(models.Model):
    """Apple's stable, app-scoped subject used to authenticate an app member."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="apple_identity")
    subject = models.CharField(max_length=255, unique=True)
    email = models.EmailField("Apple 제공 이메일", blank=True)
    cafe_nickname = models.CharField("카페 닉네임", max_length=40, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Apple 로그인 연결"
        verbose_name_plural = "Apple 로그인 연결"

    def __str__(self):
        return self.email or self.subject[:12]


class AppReviewAccount(models.Model):
    """Admin-managed demo credentials for app store review."""
    username = models.CharField("심사용 아이디", max_length=150, unique=True)
    password_hash = models.CharField("비밀번호 해시", max_length=128, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, verbose_name="앱 회원 계정", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="app_review_account",
    )
    is_active = models.BooleanField("사용", default=True)
    created_at = models.DateTimeField("생성일", auto_now_add=True)
    updated_at = models.DateTimeField("수정일", auto_now=True)

    class Meta:
        verbose_name = "앱 심사용 계정"
        verbose_name_plural = "앱 심사용 계정"
        ordering = ["-created_at", "username"]

    def __str__(self):
        return self.username

class NaverOAuthAttempt(models.Model):
    class Flow(models.TextChoices):
        APP = "app", "앱 로그인"
        PARTNER_ADMIN = "partner_admin", "협력업체 관리자 로그인"

    flow = models.CharField(max_length=20, choices=Flow.choices, default=Flow.APP)
    state_digest = models.CharField(max_length=64, unique=True)
    ticket_digest = models.CharField(max_length=64, unique=True, null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE)
    partner = models.ForeignKey(Partner, null=True, blank=True, on_delete=models.CASCADE, related_name="naver_login_attempts")
    profile_data = models.JSONField(default=dict, blank=True)
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


class AppContent(models.Model):
    class Kind(models.TextChoices):
        BANNER = "banner", "홈 제휴 배너"
        PRODUCT = "product", "쇼핑 상품"
    title = models.CharField("제목", max_length=140)
    kind = models.CharField("노출 위치", max_length=16, choices=Kind.choices)
    category = models.CharField("상품 분류", max_length=24, default="recommended", choices=[("recommended", "추천 상품"), ("groupbuy", "공동 구매"), ("benefits", "회원 혜택")])
    description = models.TextField("설명", blank=True)
    image_url = models.URLField("공개 HTTPS 이미지", max_length=2048, blank=True)
    image_data = models.BinaryField(null=True, blank=True, editable=False)
    image_content_type = models.CharField(max_length=32, blank=True, editable=False)
    asset_key = models.CharField("내장 이미지", max_length=40, blank=True, choices=[("partner-kumho", "금호타이어 · 타이어프로 제휴 배너"), ("partner-deutsch", "도이치모터스 MINI 제휴 배너"), ("partner-printtrap", "프린트랩 제휴 배너"), ("mini-october", "MINI 10월 프로모션"), ("phone-holder", "거치대"), ("grille-parts", "그릴 부품"), ("shift-knob", "기어 노브")])
    action_url = models.URLField("구매·안내 HTTPS 주소", max_length=2048, blank=True)
    price_krw = models.PositiveIntegerField("판매 금액(원)", null=True, blank=True)
    compatible_models = models.CharField("호환 차량", max_length=240, blank=True)
    is_active = models.BooleanField("공개", default=False)
    starts_at = models.DateTimeField("노출 시작", default=timezone.now)
    ends_at = models.DateTimeField("노출 종료", null=True, blank=True)
    display_order = models.PositiveSmallIntegerField("표시 순서", default=100)
    class Meta:
        verbose_name = "앱 배너·쇼핑 상품"
        verbose_name_plural = "앱 배너·쇼핑 상품"
        ordering = ["display_order", "-pk"]
    def clean(self):
        from django.core.exceptions import ValidationError
        errors = {}
        for field in ("image_url", "action_url"):
            value = getattr(self, field)
            if value and not value.startswith("https://"):
                errors[field] = "공개 HTTPS 주소를 입력해 주세요."
        if self.ends_at and self.starts_at and self.ends_at <= self.starts_at:
            errors["ends_at"] = "종료는 시작보다 늦어야 합니다."
        if errors: raise ValidationError(errors)
    def __str__(self): return self.title

class AppRelease(models.Model):
    platform = models.CharField("플랫폼", max_length=12, choices=PushDevice.Platform.choices, unique=True)
    version = models.CharField("최신 버전", max_length=32)
    build_number = models.PositiveBigIntegerField("최신 빌드 번호")
    download_url = models.URLField("업데이트 안내·스토어 HTTPS 주소", max_length=2048, blank=True)
    notes = models.TextField("변경 내용", blank=True)
    is_active = models.BooleanField("업데이트 안내 활성화", default=False)
    class Meta:
        verbose_name = "앱 업데이트 안내"
        verbose_name_plural = "앱 업데이트 안내"
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.is_active and not self.download_url.startswith("https://"):
            raise ValidationError({"download_url": "사용자가 열 수 있는 HTTPS 업데이트 주소가 필요합니다."})
    def __str__(self): return f"{self.platform} · {self.version} ({self.build_number})"

class MemberPreference(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, verbose_name="회원", on_delete=models.CASCADE, related_name="app_preference")
    primary_vehicle = models.ForeignKey(Vehicle, verbose_name="대표 차량", on_delete=models.SET_NULL, null=True, blank=True)
    class Meta:
        verbose_name = "회원 앱 설정"
        verbose_name_plural = "회원 앱 설정"

class RecordCorrectionRequest(models.Model):
    entry = models.ForeignKey(LedgerEntry, verbose_name="원본 기록", on_delete=models.PROTECT, related_name="correction_requests")
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="요청 회원", on_delete=models.PROTECT)
    reason = models.CharField("정정 요청 내용", max_length=240)
    created_at = models.DateTimeField("요청 시각", auto_now_add=True)
    resolved_entry = models.ForeignKey(LedgerEntry, verbose_name="연결된 정정 기록", on_delete=models.PROTECT, null=True, blank=True, related_name="resolved_requests")
    resolved_at = models.DateTimeField("처리 시각", null=True, blank=True)
    class Meta:
        verbose_name = "정비 기록 정정 요청"
        verbose_name_plural = "정비 기록 정정 요청"
        ordering = ["-created_at"]
        constraints = [models.UniqueConstraint(fields=["entry", "requested_by"], condition=models.Q(resolved_at__isnull=True), name="one_open_record_correction")]
    def __str__(self): return f"기록 {self.entry_id} · {'처리 완료' if self.resolved_at else '처리 대기'}"

class MaintenanceRecommendation(models.Model):
    entry = models.ForeignKey(LedgerEntry, on_delete=models.PROTECT, related_name='recommendations')
    member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField('교체 항목', max_length=100)
    due_date = models.DateField('권장 교체일', null=True, blank=True)
    due_odometer_km = models.PositiveIntegerField('권장 교체 주행거리', null=True, blank=True)
    status = models.CharField(max_length=12, choices=[('pending','회원 확인 대기'),('accepted','알림 등록'),('declined','거절')], default='pending')
    reminder = models.OneToOneField(Reminder, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = '다음 교체 권장'
        verbose_name_plural = '다음 교체 권장'

class ServiceEstimate(models.Model):
    booking = models.ForeignKey(PartnerBooking, on_delete=models.PROTECT, related_name='estimates')
    revision = models.PositiveIntegerField('견적 버전', default=1)
    items = models.JSONField('견적 항목', default=list)
    total_krw = models.PositiveIntegerField('견적 총액', default=0)
    note = models.TextField('안내사항', blank=True)
    status = models.CharField(max_length=12, choices=[('draft','작성 중'),('sent','회원 동의 대기'),('accepted','회원 동의'),('declined','회원 거절'),('superseded','새 견적으로 대체')], default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = '정비 견적'
        verbose_name_plural = '정비 견적'
        constraints = [models.UniqueConstraint(fields=['booking','revision'], name='unique_booking_estimate_revision')]

class AppRuntimeSettings(models.Model):
    refresh_interval_seconds = models.PositiveSmallIntegerField('사용 중 변경 확인 주기(초)', default=15,
        validators=[MinValueValidator(10), MaxValueValidator(120)])
    show_demo_products = models.BooleanField('상품 미등록 시 데모 이미지 표시', default=True)
    public_revision = models.PositiveBigIntegerField(default=1, editable=False)
    member_revision = models.PositiveBigIntegerField(default=1, editable=False)
    class Meta:
        verbose_name = '앱 연동 설정'
        verbose_name_plural = '앱 연동 설정'
    def __str__(self): return '앱 자동 갱신·데모 표시 설정'
