Warning: truncated output (original token count: 8432)
Total output lines: 636

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
        verbose_name_plural = "…2432 tokens truncated… = models.CharField(max_length=500, blank=True)
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
    asset_key = models.CharField("내장 이미지", max_length=40, blank=True, choices=[("mini-october", "MINI 10월 프로모션"), ("phone-holder", "거치대"), ("grille-parts", "그릴 부품"), ("shift-knob", "기어 노브")])
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
        if self.is_active and self.kind == self.Kind.PRODUCT and not self.action_url:
            errors["action_url"] = "실제 구매·안내 주소를 입력해야 상품을 공개할 수 있습니다."
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
