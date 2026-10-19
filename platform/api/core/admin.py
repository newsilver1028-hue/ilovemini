Warning: truncated output (original token count: 8355)
Total output lines: 654

from django.core.exceptions import ObjectDoesNotExist
from django.utils.html import format_html
from django import forms
from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.db.models import IntegerField, OuterRef, Subquery, Sum, Value
from django.db.models.functions import Coalesce
from django.urls import path
from .member_display import member_nickname, member_label, MemberAutocompleteView, MemberAutocompleteSelect

from .models import (
    LedgerEntry, Notice, Offer, Partner, PartnerImage, PartnerReview, PartnerStaff, PushDevice, Reminder, Vehicle, VehiclePlateHistory,
    VehicleOwnership, VehicleTransferCode, AttendanceCheckin, PointTransaction, PointRedemptionRequest,
    SeasonBanner, AppContent, AppRelease, MemberPreference, RecordCorrectionRequest, AppReviewAccount,
)


admin.site.site_header = "아이러브미니 운영 관리"
admin.site.site_title = "ILOVEMINI 운영자"
admin.site.index_title = "앱 콘텐츠와 회원 데이터 관리"


class NoticeAdminForm(forms.ModelForm):
    class Meta:
        model = Notice
        fields = "__all__"

    def clean(self):
        cleaned = super().clean()
        published_at = cleaned.get("published_at")
        expires_at = cleaned.get("expires_at")
        if published_at and expires_at and expires_at <= published_at:
            self.add_error("expires_at", "종료 시각은 게시 시각보다 늦어야 합니다.")
        return cleaned


class PartnerAdminForm(forms.ModelForm):
    description = forms.CharField(label="업체 소개 글", required=False,
        help_text="앱의 업체 상세 → 사진 아래 ‘업체 소개’에 표시됩니다. 소개 문구를 자유롭게 작성하세요.",
        widget=forms.Textarea(attrs={"rows": 6, "cols": 70, "placeholder": "매장의 특징, 전문 서비스, 고객에게 전하고 싶은 내용을 작성하세요."}))
    business_info = forms.CharField(label="매장 상세 안내", required=False,
        help_text="앱의 업체 상세 → ‘업체 정보’에 표시됩니다. 방문·주차·이용 안내 등을 작성하세요.",
        widget=forms.Textarea(attrs={"rows": 5, "cols": 70}))
    storefront_photo_url = forms.URLField(label="대표 사진 주소 (선택)", required=False,
        help_text="사진 파일 첨부는 아래 ‘매장 사진’에서 가능합니다. 주소가 있는 대표 사진만 이곳에 입력하세요.")
    service_categories = forms.CharField(
        required=False,
        help_text="여러 항목은 쉼표로 구분해 입력하세요. 예: 정비, 튜닝, 부품",
    )

    class Meta:
        model = Partner
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        categories = self.initial.get("service_categories", [])
        if isinstance(categories, list):
            self.initial["service_categories"] = ", ".join(categories)

    def clean_service_categories(self):
        value = self.cleaned_data["service_categories"]
        return list(dict.fromkeys(item.strip() for item in value.split(",") if item.strip()))


class OfferAdminForm(forms.ModelForm):
    class Meta:
        model = Offer
        fields = "__all__"

    def clean(self):
        cleaned = super().clean()
        starts_at = cleaned.get("starts_at")
        ends_at = cleaned.get("ends_at")
        if starts_at and ends_at and ends_at <= starts_at:
            self.add_error("ends_at", "종료 시각은 시작 시각보다 늦어야 합니다.")
        return cleaned


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ("id", "current_owner", "model_name", "plate_number", "model_year", "current_odometer_km", "public_id", "created_at")
    list_filter = ("model_year",)
    search_fields = ("ownerships__user__username", "ownerships__user__email", "model_name", "nickname", "generation", "plate_number", "vin_hash")
    readonly_fields = ("public_id", "created_at")
    date_hierarchy = "created_at"

    @admin.display(description="현재 등록 사용자")
    def current_owner(self, obj):
        return obj.owner or "미지정"

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop("delete_selected", None)
        return actions

    def has_delete_permission(self, request, obj=None):
        if obj and obj.ledger_entries.filter(source=LedgerEntry.Source.PARTNER).exists():
            return False
        return super().has_delete_permission(request, obj)


@admin.register(VehiclePlateHistory)
class VehiclePlateHistoryAdmin(admin.ModelAdmin):
    list_display = ("vehicle", "plate_number", "started_at", "ended_at", "changed_by")
    search_fields = ("plate_number", "vehicle__model_name", "changed_by__username")
    readonly_fields = tuple(field.name for field in VehiclePlateHistory._meta.fields)
    date_hierarchy = "started_at"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop("delete_selected", None)
        return actions


@admin.register(VehicleOwnership)
class VehicleOwnershipAdmin(admin.ModelAdmin):
    list_display = ("vehicle", "user", "relationship", "started_at", "ended_at", "verification_method", "verification_status")
    list_filter = ("relationship", "verification_status", "verification_method")
    search_fields = ("vehicle__model_name", "user__username", "user__email")
    readonly_fields = tuple(field.name for field in VehicleOwnership._meta.fields)
    date_hierarchy = "started_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):
    list_display = ("entry_date", "vehicle", "kind", "source", "partner", "amount_krw", "odometer_km", "description")
    list_filter = ("source", "partner", "kind", "entry_date")
    search_fields = ("vehicle__model_name", "vehicle__nickname", "description", "part_number")
    date_hierarchy = "entry_date"

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.source == LedgerEntry.Source.PARTNER:
            return tuple(field.name for field in LedgerEntry._meta.fields)
        return ("source", "partner", "verified_by", "verified_at", "record_hash", "corrects", "correction_reason", "created_at")

    def has_delete_permission(self, request, obj=None):
        if obj and obj.source == LedgerEntry.Source.PARTNER:
            return False
        return super().has_delete_permission(request, obj)

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop("delete_selected", None)
        return actions

    def delete_queryset(self, request, queryset):
        queryset.exclude(source=LedgerEntry.Source.PARTNER).delete()


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ("title", "vehicle", "due_date", "due_odometer_km", "completed_at", "notification_sent_at")
    list_filter = ("completed_at", "due_date")
    search_fields = ("title", "vehicle__model_name", "vehicle__nickname")
    date_hierarchy = "created_at"
    readonly_fields = ("created_at", "notification_sent_at")


@admin.register(AttendanceCheckin)
class AttendanceCheckinAdmin(admin.ModelAdmin):
    list_display = ("checkin_date", "member", "points_awarded", "created_at")
    list_filter = ("checkin_date",)
    search_fields = ("user__username", "user__email", "user__naver_identity__nickname", "user__naver_identity__cafe_nickname")
    list_select_related = ("user__naver_identity",)
    readonly_fields = tuple(field.name for field in AttendanceCheckin._meta.fields)
    date_hierarchy = "checkin_date"

    @admin.display(description="회원")
    def member(self, obj):
        return member_label(obj.user)

    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False


@admin.register(PointTransaction)
class PointTransactionAdmin(admin.ModelAdmin):
    list_display = ("created_at", "member", "transaction_type", "points_delta", "available_at", "partner", "ledger_entry", "memo")
    list_filter = ("transaction_type", "created_at", "available_at", "partner")
    search_fields = ("user__username", "user__email", "user__naver_identity__nickname", "user__naver_identity__cafe_nickname", "memo", "idempotency_key")
    list_select_related = ("user__naver_identity", "partner", "ledger_entry")
    readonly_fields = tuple(field.name for field in PointTransaction._meta.fields)
    date_hierarchy = "created_at"

    @admin.display(description="회원")
    def member(self, obj):
        return member_label(obj.user)

    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False


@admin.register(PointRedemptionRequest)
class PointRedemptionRequestAdmin(admin.ModelAdmin):
    list_display = ("created_at", "member_label", "partner", "payment_amount_krw", "points_requested", "status", "expires_at", "responded_at", "completed_at")
    list_filter = ("status", "created_at", "partner")
    search_fields = ("member__username", "member__email", "member__naver_identity__nickname", "member__naver_identity__cafe_nickname", "partner__name", "partner__branch_label")
    list_select_related = ("member__naver_identity", "partner", "transaction")
    readonly_fields = tuple(field.name for field in PointRedemptionRequest._meta.fields)
    date_hierarchy = "created_at"

    @admin.display(description="회원")
    def member_label(self, obj):
        return member_label(obj.member)

    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False


class OfferInline(admin.TabularInline):
    model = Offer
    form = OfferAdminForm
    extra = 0
    fields = ("title", "is_active", "starts_at", "ends_at", "description", "redemption_instructions")


@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    form = NoticeAdminForm
    list_display = ("title", "category", "is_published", "is_pinned", "published_at", "expires_at")
    list_editable = ("is_published", "is_pinned")
    list_filter = ("is_published", "is_pinned", "category")
    search_fields = ("title", "summary", "body")
    date_hierarchy = "published_at"
    save_on_top = True
    fieldsets = (
        ("공지 내용", {"fields": ("title", "summary", "body", "category", "original_url")}),
        ("게시 일정 및 노출", {"fields": ("published_at", "expires_at", "is_published", "is_pinned")}),
    )


class PartnerImageAdminForm(forms.ModelForm):
    upload = forms.FileField(label="소개 이미지 첨부", required=False,
        help_text="PNG, JPEG, WebP 파일을 선택하세요. 최대 5MB. 기존 이미지를 바꾸려면 새 파일을 선택하세요.",
        widget=forms.ClearableFileInput(attrs={"accept": "image/png,image/jpeg,image/webp"}))

    class Meta:
        model = PartnerImage
        fields = ("partner", "caption", "display_order")

    def clean(self):
        cleaned = super().clean()
        upload = cleaned.get("upload")
        if upload:
            if upload.size > 5 * 1024 * 1024:
                self.add_error("upload", "이미지는 5MB 이하로 첨부해 주세요.")
                return cleaned
            data = upload.read()
            mime = ""
            if data.s…2355 tokens truncated…et_queryset(request).select_related("naver_identity")
                .prefetch_related("partner_memberships__partner", "groups")
                .annotate(_point_balance=Coalesce(Subquery(point_total, output_field=IntegerField()), Value(0))))
    actions = [grade_action(code) for code in GRADES] + ["export_members_csv"]

    @admin.display(description="소속 협력업체")
    def display_workplaces(self, obj):
        names = [staff.partner.name for staff in obj.partner_memberships.all() if staff.is_active and staff.partner.is_active]
        return " / ".join(names) or "—"

    @admin.display(description="포인트 잔액", ordering="_point_balance")
    def display_points_balance(self, obj):
        return f"{obj._point_balance:,}P"

    @admin.action(description="선택한 회원 목록 CSV 다운로드")
    def export_members_csv(self, request, queryset):
        import csv
        from django.http import HttpResponse
        from django.core.exceptions import PermissionDenied
        if not self.has_module_permission(request):
            raise PermissionDenied
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="ilovemini-members.csv"'
        response.write("\ufeff")
        writer = csv.writer(response)
        writer.writerow(["회원번호", "닉네임", "회원 이름", "이메일", "프로필 사진", "성별", "생일", "연령대", "출생연도", "휴대전화번호", "회원등급", "소속 협력업체", "활성화", "가입일", "최근 로그인"])
        def safe(value):
            value = str(value or "")
            return "'" + value if value.lstrip().startswith(("=", "+", "-", "@")) else value
        for user in queryset:
            writer.writerow([user.pk, safe(member_nickname(user)), safe(user.get_full_name()), safe(user.email), *[safe(getattr(getattr(user, "naver_identity", None), key, "")) for key in ("profile_image", "gender", "birthday", "age", "birthyear", "mobile")], GRADES[member_grade(user)], safe(self.display_workplaces(user)), user.is_active, user.date_joined.isoformat(), user.last_login.isoformat() if user.last_login else ""])
        return response

    @admin.display(description="회원 등급")
    def ilovemini_grade(self, obj):
        return GRADES[member_grade(obj)]

    def has_module_permission(self, request):
        return request.user.is_active and request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_add_permission(self, request):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_delete_permission(self, request, obj=None):
        return self.has_module_permission(request) and (obj is None or obj.pk != request.user.pk)


# Korean labels are limited to administrator presentation.
_MODEL_LABELS = {
    Vehicle: "등록 차량", VehicleOwnership: "차량 소유 이력",
    VehiclePlateHistory: "차량 번호 변경 이력", VehicleTransferCode: "차량 인계 코드",
    LedgerEntry: "차계부 기록", Reminder: "차량 관리 알림",
    AttendanceCheckin: "출석 기록", PointTransaction: "포인트 거래 내역",
    PointRedemptionRequest: "포인트 사용 승인 요청",
    Notice: "공지사항", Partner: "협력업체", PartnerStaff: "협력업체 담당자",
    Offer: "제휴 혜택", PushDevice: "알림 수신 기기",
    PartnerImage: "업체 소개 사진", PartnerReview: "업체 리뷰",
    SeasonBanner: "앱 시작 시즌 배너", AppContent: "앱 콘텐츠",
    AppRelease: "앱 업데이트 안내", MemberPreference: "회원 앱 설정",
    RecordCorrectionRequest: "정비 기록 정정 요청",
}
_FIELD_LABELS = {
    "id": "번호", "user": "회원 계정", "partner": "소속 협력업체", "vehicle": "차량",
    "can_verify_records": "QR 차량 조회·인증 기록 등록 허용",
    "can_manage_bookings": "예약 관리 허용", "is_active": "활성화",
    "name": "업체명", "branch_label": "지점명", "region": "지역",
    "service_categories": "서비스 분야", "description": "설명",
    "address": "주소", "phone": "전화번호", "hours": "영업시간",
    "cafe_url": "업체별 카페 게시판 주소", "map_url": "지도 주소",
    "is_sponsored": "광고 제휴 업체", "display_order": "표시 순서",
    "title": "제목", "summary": "요약", "body": "내용", "category": "분류",
    "original_url": "원문 주소", "is_pinned": "상단 고정",
    "published_at": "게시 시각", "expires_at": "만료 시각", "is_published": "공개",
    "starts_at": "시작 시각", "ends_at": "종료 시각",
    "redemption_instructions": "혜택 이용 방법", "created_at": "등록 시각", "updated_at": "수정 시각",
    "nickname": "차량 별명", "model_name": "차종", "generation": "세대", "manufacturer": "제조사",
    "model_year": "연식", "plate_number": "차량 번호", "first_registration_date": "최초 등록일",
    "vin_hash": "차대번호 해시", "public_id": "차량 고유 ID", "passport_public": "차량 이력 공개",
    "status": "상태", "current_odometer_km": "현재 주행거리(km)",
    "started_at": "시작 시각", "ended_at": "종료 시각", "changed_by": "변경한 회원",
    "verification_method": "확인 방법", "verification_status": "소유 확인 상태", "relationship": "차량 이용 관계",
    "previous_owner": "이전 차주", "new_owner": "새 차주", "accepted_at": "인계 완료 시각",
    "invalidated_at": "무효화 시각", "kind": "기록 종류", "entry_date": "기록일",
    "odometer_km": "주행거리(km)", "amount_krw": "금액(원)", "quantity_liters": "주유량(L)",
    "source": "기록 출처", "verified_by": "인증 담당자", "verified_at": "인증 시각",
    "part_number": "부품 번호", "evidence_url": "증빙 주소", "record_hash": "기록 검증 해시",
    "corrects": "정정 대상", "correction_reason": "정정 사유", "due_date": "예정일",
    "due_odometer_km": "예정 주행거리(km)", "completed_at": "완료 시각",
    "notification_sent_at": "알림 발송 시각", "installation_id": "설치 식별자", "platform": "기기 종류",
    "asset_key": "내장 이미지", "subtitle": "부제목", "image_url": "이미지 주소",
    "is_active": "사용", "starts_at": "시작 시각", "ends_at": "종료 시각",
    "duration_seconds": "표시 시간(초)", "priority": "우선순위", "manufacturer": "제조사",
    "first_registration_date": "최초 등록일", "passport_public": "차량 이력 공개",
    "code_digest": "인계 코드 해시", "expires_at": "만료 시각", "consumed_at": "사용 시각",
    "image_data": "이미지 데이터", "content_type": "파일 형식", "file_name": "파일 이름",
    "updated_at": "수정 시각", "caption": "이미지 설명", "display_order": "표시 순서",
    "rating": "평점", "comment": "리뷰 내용", "representative_name": "대표자 이름",
    "representative_title": "대표자 직함", "representative_experience_years": "정비 경력(년)",
    "representative_photo_url": "대표자 사진 주소", "storefront_photo_url": "매장 대표 사진 주소",
    "business_info": "매장 상세 안내", "is_sponsored": "광고 제휴 업체", "hours": "영업시간",
    "customer": "예약 회원", "requested_at": "예약 요청 시각", "scheduled_at": "예약 희망 시각",
    "service_type": "요청 정비 항목", "customer_note": "회원 요청 사항", "contact_phone": "연락처",
    "partner_note": "업체 답변", "marketing_opt_in": "마케팅 수신 동의",
    "terms_accepted_at": "이용약관 동의 시각", "privacy_accepted_at": "개인정보 동의 시각",
    "subject": "네이버 회원 식별값", "cafe_nickname": "네이버 카페 닉네임",
    "profile_data": "프로필 정보", "provider_subject": "네이버 회원 식별값",
    "nickname": "닉네임", "profile_image": "프로필 사진", "gender": "성별",
    "birthday": "생일", "age": "연령대", "birthyear": "출생연도", "mobile": "휴대전화번호",
    "points_awarded": "적립 포인트", "streak_days": "연속 출석 일수",
    "checkin_date": "출석일",
    "transaction_type": "거래 종류", "points_delta": "포인트 변동", "available_at": "사용 가능 시각",
    "memo": "처리 내용", "idempotency_key": "중복 방지 키", "ledger_entry": "정비 기록",
    "payment_amount_krw": "결제 금액(원)", "points_requested": "사용 요청 포인트",
    "responded_at": "회원 응답 시각", "completed_at": "사용 완료 시각",
    "transaction": "포인트 거래", "member": "회원", "primary_vehicle": "대표 차량",
}
for _model, _label in _MODEL_LABELS.items():
    _model._meta.verbose_name = _label
    _model._meta.verbose_name_plural = _label
    for _field in _model._meta.fields:
        if _field.name in _FIELD_LABELS:
            _field.verbose_name = _FIELD_LABELS[_field.name]
PartnerStaff._meta.get_field("can_verify_records").help_text = "담당자가 앱에서 QR로 차량을 조회하고 업체 인증 정비기록을 등록할 수 있습니다."
PartnerStaff._meta.get_field("can_manage_bookings").help_text = "소속 업체의 예약을 확인하고 처리할 수 있습니다."
PartnerStaff._meta.get_field("is_active").help_text = "담당자와 소속 업체가 모두 활성화되어야 협력업체 등급으로 인식합니다."
PartnerAdminForm.base_fields["service_categories"].label = "서비스 분야"
admin.site.index_title = "운영 대시보드"


User._meta.verbose_name = "가입 회원"
User._meta.verbose_name_plural = "가입 회원 목록"
User._meta.get_field("id").verbose_name = "회원 번호"
Group._meta.get_field("id").verbose_name = "번호"

@admin.register(SeasonBanner)
class SeasonBannerAdmin(admin.ModelAdmin):
    list_display = ("title", "is_active", "starts_at", "ends_at", "duration_seconds", "priority")
    list_filter = ("is_active",)
    search_fields = ("title", "subtitle")
    date_hierarchy = "starts_at"
@admin.register(AppContent)
class AppContentAdmin(admin.ModelAdmin):
    list_display = ("title", "kind", "category", "is_active", "display_order", "starts_at", "ends_at")
    list_filter = ("kind", "category", "is_active")
    search_fields = ("title", "description", "compatible_models")
    date_hierarchy = "starts_at"
@admin.register(AppRelease)
class AppReleaseAdmin(admin.ModelAdmin):
    list_display = ("platform", "version", "build_number", "is_active")
@admin.register(MemberPreference)
class MemberPreferenceAdmin(admin.ModelAdmin):
    list_display = ("member", "primary_vehicle")
    list_select_related = ("user__naver_identity", "primary_vehicle")
    readonly_fields = ("user", "primary_vehicle")
    @admin.display(description="회원")
    def member(self, obj): return member_label(obj.user)
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
@admin.register(RecordCorrectionRequest)
class RecordCorrectionRequestAdmin(admin.ModelAdmin):
    list_display = ("entry", "member", "reason", "created_at", "resolved_at")
    list_select_related = ("requested_by__naver_identity", "entry")
    list_filter = ("resolved_at",)
    date_hierarchy = "created_at"
    readonly_fields = ("entry", "requested_by", "reason", "created_at", "resolved_entry", "resolved_at")
    @admin.display(description="요청 회원")
    def member(self, obj): return member_label(obj.requested_by)
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False


# Register app review account management after the core admin models.
from . import review_admin as _review_admin
