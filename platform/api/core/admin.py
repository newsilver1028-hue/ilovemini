from django.core.exceptions import ObjectDoesNotExist
from django import forms
from django.contrib import admin
from django.urls import path
from .member_display import member_nickname, member_label, MemberAutocompleteView, MemberAutocompleteSelect

from .models import (
    LedgerEntry, Notice, Offer, Partner, PartnerStaff, PushDevice, Reminder, Vehicle, VehiclePlateHistory,
    VehicleOwnership, VehicleTransferCode,
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


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    form = PartnerAdminForm
    list_display = ("name", "branch_label", "region", "is_active", "is_sponsored", "display_order")
    list_editable = ("is_active", "is_sponsored", "display_order")
    list_filter = ("is_active", "is_sponsored", "region")
    search_fields = ("name", "branch_label", "region", "description", "address")
    save_on_top = True
    inlines = (OfferInline,)
    fieldsets = (
        ("업체 소개", {"fields": ("name", "branch_label", "region", "service_categories", "description")}),
        ("연락처 및 연결", {"fields": ("address", "phone", "hours", "cafe_url", "map_url")}),
        ("앱 노출 설정", {"fields": ("is_active", "is_sponsored", "display_order")}),
    )


@admin.register(PartnerStaff)
class PartnerStaffAdmin(admin.ModelAdmin):
    autocomplete_fields = ("user",)

    def get_urls(self):
        return [path("member-autocomplete/", self.admin_site.admin_view(MemberAutocompleteView.as_view(admin_site=self.admin_site)), name="core_partnerstaff_member_autocomplete")] + super().get_urls()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "user":
            kwargs["widget"] = MemberAutocompleteSelect(db_field.remote_field, self.admin_site)
            kwargs["queryset"] = db_field.remote_field.model.objects.select_related("naver_identity")
            field = super().formfield_for_foreignkey(db_field, request, **kwargs)
            field.label_from_instance = member_label
            return field
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    @admin.display(description="회원 계정")
    def member_account(self, obj):
        return member_label(obj.user)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user__naver_identity", "partner")
    list_display = ("member_account", "partner", "can_verify_records", "can_manage_bookings", "is_active", "created_at")
    list_editable = ("can_verify_records", "can_manage_bookings", "is_active")
    list_filter = ("partner", "can_verify_records", "can_manage_bookings", "is_active")
    search_fields = ("user__username", "user__email", "user__naver_identity__nickname", "=user__id", "partner__name")
    readonly_fields = ("created_at",)


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    form = OfferAdminForm
    list_display = ("title", "partner", "is_active", "starts_at", "ends_at")
    list_editable = ("is_active",)
    list_filter = ("is_active", "partner")
    search_fields = ("title", "description", "partner__name")
    date_hierarchy = "starts_at"
    save_on_top = True


@admin.register(PushDevice)
class PushDeviceAdmin(admin.ModelAdmin):
    list_display = ("user", "platform", "updated_at")
    list_filter = ("platform",)
    search_fields = ("user__username", "user__email", "installation_id")
    readonly_fields = ("user", "installation_id", "platform", "created_at", "updated_at")
    date_hierarchy = "updated_at"

    def has_add_permission(self, request):
        return False


@admin.register(VehicleTransferCode)
class VehicleTransferCodeAdmin(admin.ModelAdmin):
    list_display = ("vehicle", "previous_owner", "new_owner", "created_at", "expires_at", "accepted_at", "invalidated_at")
    list_filter = ("accepted_at", "invalidated_at", "created_at")
    search_fields = ("vehicle__model_name", "previous_owner__username", "new_owner__username")
    readonly_fields = tuple(field.name for field in VehicleTransferCode._meta.fields if field.name != "code_digest")
    exclude = ("code_digest",)
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# Grade changes are restricted to operators; staff cannot promote themselves.
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.core.exceptions import ValidationError
from .member_roles import GRADES, assign_member_grade, member_grade


def grade_action(code):
    @admin.action(description=f"회원 등급을 {GRADES[code]}(으)로 변경")
    def action(modeladmin, request, queryset):
        for user in queryset:
            try:
                assign_member_grade(request.user, user, code)
                modeladmin.log_change(request, user, f"회원 등급: {GRADES[code]}")
            except ValidationError as exc:
                modeladmin.message_user(request, f"{user}: {' '.join(exc.messages)}", level="ERROR")
    action.__name__ = f"set_grade_{code}"
    return action


class NaverProfileInline(admin.StackedInline):
    from .models import NaverIdentity
    model = NaverIdentity
    verbose_name = "네이버 회원정보"
    verbose_name_plural = "네이버 회원정보 (네이버가 제공한 항목)"
    fields = ("name", "email", "nickname", "profile_image", "gender", "birthday", "age", "birthyear", "mobile")
    readonly_fields = fields
    extra = 0
    can_delete = False
    def has_add_permission(self, request, obj=None):
        return False


User = get_user_model()
admin.site.unregister(User)


@admin.register(User)
class MemberUserAdmin(UserAdmin):
    inlines = (NaverProfileInline,)
    list_display = ("id", "display_nickname", "display_member_name", "email", "display_mobile", "ilovemini_grade", "display_workplaces", "is_active", "date_joined", "last_login")
    search_fields = ("naver_identity__nickname", "email", "username", "first_name", "last_name", "naver_identity__mobile", "=id")
    list_per_page = 50
    ordering = ("-date_joined", "-id")
    list_filter = ("is_active", "is_staff", "is_superuser", "groups")
    readonly_fields = (*UserAdmin.readonly_fields, "display_nickname", "id", "display_workplaces")
    fieldsets = (("회원 식별 정보", {"fields": ("id", "display_nickname", "display_workplaces")}),) + UserAdmin.fieldsets

    @admin.display(description="휴대전화번호")
    def display_mobile(self, obj):
        try:
            return obj.naver_identity.mobile or "—"
        except ObjectDoesNotExist:
            return "—"

    @admin.display(description="회원 이름")
    def display_member_name(self, obj):
        return obj.get_full_name() or "이름 미제공"

    @admin.display(description="닉네임")
    def display_nickname(self, obj):
        return member_nickname(obj)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("naver_identity").prefetch_related("partner_memberships__partner", "groups")
    actions = [grade_action(code) for code in GRADES] + ["export_members_csv"]

    @admin.display(description="소속 협력업체")
    def display_workplaces(self, obj):
        names = [staff.partner.name for staff in obj.partner_memberships.all() if staff.is_active and staff.partner.is_active]
        return " / ".join(names) or "—"

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
    Notice: "공지사항", Partner: "협력업체", PartnerStaff: "협력업체 담당자",
    Offer: "제휴 혜택", PushDevice: "알림 수신 기기",
}
_FIELD_LABELS = {
    "id": "번호", "user": "회원 계정", "partner": "소속 협력업체", "vehicle": "차량",
    "can_verify_records": "QR 차량 조회·인증 기록 등록 허용",
    "can_manage_bookings": "예약 관리 허용", "is_active": "활성화",
    "name": "업체명", "branch_label": "지점명", "region": "지역",
    "service_categories": "서비스 분야", "description": "설명",
    "address": "주소", "phone": "전화번호", "hours": "영업시간",
    "cafe_url": "카페 게시글 주소", "map_url": "지도 주소",
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
admin.site.index_title = "회원 등급: 사용자 목록 → 회원 선택 → 동작 → 등급 변경 / 업체 권한: 협력업체 담당자 → 추가"


User._meta.verbose_name = "가입 회원"
User._meta.verbose_name_plural = "가입 회원 목록"
