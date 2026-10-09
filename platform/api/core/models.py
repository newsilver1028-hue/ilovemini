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
    installation_id = models.CharField(max_length=2048, unique=True)
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
    name = models.CharField(max_length=120)
    branch_label = models.CharField(max_length=80, blank=True, default="")
    region = models.CharField(max_length=80, blank=True)
    service_categories = models.JSONField(default=list, blank=True)
    description = models.TextField(blank=True)
    address = models.CharField(max_length=240, blank=True)
    phone = models.CharField(max_length=40, blank=True)
    hours = models.CharField(max_length=160, blank=True)
    cafe_url = models.URLField(blank=True)
    map_url = models.URLField(blank=True)
    storefront_photo_url = models.URLField(max_length=2048, blank=True)
    business_info = models.TextField(blank=True)
    representative_name = models.CharField(max_length=100, blank=True)
    representative_title = models.CharField(max_length=100, blank=True)
    representative_experience_years = models.PositiveSmallIntegerField(null=True, blank=True)
    representative_photo_url = models.URLField(max_length=2048, blank=True)
    is_sponsored = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    display_order = models.PositiveSmallIntegerField(default=100)

    class Meta:
        ordering = ["display_order", "name"]
        constraints = [models.UniqueConstraint(fields=["name", "branch_label"], name="unique_partner_name_branch")]

    def __str__(self):
        return f"{self.name} · {self.branch_label}" if self.branch_label else self.name


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

class NaverOAuthAttempt(models.Model):
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
        verbose_name = "회원 대표 차량"
        verbose_name_plural = "회원 대표 차량"

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
