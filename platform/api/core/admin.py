from django import forms
from django.contrib import admin

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
    list_display = ("user", "partner", "can_verify_records", "can_manage_bookings", "is_active", "created_at")
    list_editable = ("can_verify_records", "can_manage_bookings", "is_active")
    list_filter = ("partner", "can_verify_records", "can_manage_bookings", "is_active")
    search_fields = ("user__username", "user__email", "partner__name")
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


User = get_user_model()
admin.site.unregister(User)


@admin.register(User)
class MemberUserAdmin(UserAdmin):
    list_display = (*UserAdmin.list_display, "ilovemini_grade")
    actions = [grade_action(code) for code in GRADES]

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
