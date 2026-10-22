from datetime import date, datetime, time, timedelta
from django.core.exceptions import ObjectDoesNotExist
from django.utils.html import format_html
from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import AdminDateWidget, AdminSplitDateTime
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.db import models
from django.db.models import IntegerField, OuterRef, Subquery, Sum, Value
from django.db.models import Count
from django.db.models.functions import Coalesce, TruncDate
from django.http import JsonResponse
from django.urls import path, reverse
from django.utils import timezone
from .member_display import member_nickname, member_label, MemberAutocompleteView, MemberAutocompleteSelect

from .models import (
    LedgerEntry, Notice, Offer, Partner, PartnerImage, PartnerReview, PartnerStaff, PushDevice, Reminder, Vehicle, VehiclePlateHistory,
    VehicleOwnership, VehicleTransferCode, AttendanceCheckin, PointTransaction, PointRedemptionRequest,
    SeasonBanner, AppContent, AppRelease, MemberPreference, RecordCorrectionRequest, AppReviewAccount, AppleIdentity,
    PartnerServiceCategoryOption,
)


admin.site.site_header = "아이러브미니 운영 관리"
admin.site.site_title = "ILOVEMINI 운영자"
admin.site.index_title = "앱 콘텐츠와 회원 데이터 관리"


class AdminCalendarMixin:
    """Add date pickers to forms and a small date browser to each model list."""

    change_list_template = "admin/core/change_list_with_calendar.html"
    calendar_weekdays = ("월", "화", "수", "목", "금", "토", "일")

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        field = super().formfield_for_dbfield(db_field, request, **kwargs)
        if field is None:
            return None
        if isinstance(db_field, models.DateTimeField):
            previous = getattr(field.widget, "widgets", ())
            widget = AdminSplitDateTime()
            for new_widget, old_widget in zip(widget.widgets, previous):
                new_widget.attrs.update(old_widget.attrs)
            field.widget = widget
        elif isinstance(db_field, models.DateField):
            attrs = dict(getattr(field.widget, "attrs", {}))
            field.widget = AdminDateWidget(attrs=attrs)
        return field

    def _calendar_date_field(self):
        if self.date_hierarchy:
            try:
                field = self.model._meta.get_field(self.date_hierarchy)
                if isinstance(field, models.DateField):
                    return field
            except LookupError:
                pass
        return next((field for field in self.model._meta.fields if isinstance(field, models.DateField)), None)

    def _calendar_context(self, request):
        date_field = self._calendar_date_field()
        if date_field is None:
            return {"show_calendar": False}

        today = timezone.localdate()
        try:
            year = int(request.GET.get("calendar_year", today.year))
            month = int(request.GET.get("calendar_month", today.month))
            if month < 1 or month > 12 or year < 1900 or year > 9998:
                raise ValueError
        except (TypeError, ValueError):
            year, month = today.year, today.month

        month_start = date(year, month, 1)
        next_month = date(year + (month == 12), 1 if month == 12 else month + 1, 1)
        previous_month = date(year - (month == 1), 12 if month == 1 else month - 1, 1)
        grid_start = month_start - timedelta(days=month_start.weekday())
        field_name = date_field.name
        queryset = self.get_queryset(request)

        if isinstance(date_field, models.DateTimeField):
            start_at = timezone.make_aware(datetime.combine(month_start, time.min), timezone.get_current_timezone())
            end_at = timezone.make_aware(datetime.combine(next_month, time.min), timezone.get_current_timezone())
            queryset = queryset.filter(**{f"{field_name}__gte": start_at, f"{field_name}__lt": end_at})
            daily_counts = {
                row["calendar_day"]: row["count"]
                for row in queryset.annotate(
                    calendar_day=TruncDate(field_name, tzinfo=timezone.get_current_timezone())
                ).values("calendar_day").annotate(count=Count("pk"))
            }
            date_filter = f"{field_name}__date"
        else:
            queryset = queryset.filter(**{f"{field_name}__gte": month_start, f"{field_name}__lt": next_month})
            daily_counts = {
                row[field_name]: row["count"]
                for row in queryset.values(field_name).annotate(count=Count("pk"))
            }
            date_filter = f"{field_name}__exact"

        def calendar_url(*, target_month=None, target_day=None):
            params = request.GET.copy()
            for key in list(params):
                if key in {"calendar_year", "calendar_month", "p"} or key.startswith(f"{field_name}__"):
                    params.pop(key, None)
            if target_month:
                params["calendar_year"] = str(target_month.year)
                params["calendar_month"] = str(target_month.month)
            if target_day:
                params[date_filter] = target_day.isoformat()
            suffix = params.urlencode()
            return f"{request.path}?{suffix}" if suffix else request.path

        weeks = []
        current_day = grid_start
        while len(weeks) < 6:
            week = []
            for _ in range(7):
                week.append({
                    "date": current_day,
                    "in_month": current_day.month == month_start.month,
                    "is_today": current_day == today,
                    "count": daily_counts.get(current_day, 0),
                    "url": calendar_url(target_month=month_start, target_day=current_day),
                })
                current_day += timedelta(days=1)
            weeks.append(week)

        return {
            "show_calendar": True,
            "calendar_month": month_start,
            "calendar_field_label": date_field.verbose_name,
            "calendar_prev_url": calendar_url(target_month=previous_month),
            "calendar_today_url": calendar_url(target_month=today.replace(day=1)),
            "calendar_next_url": calendar_url(target_month=next_month),
            "calendar_weeks": weeks,
            "calendar_weekdays": self.calendar_weekdays,
        }

    def get_changelist_instance(self, request):
        changelist = super().get_changelist_instance(request)
        if not self.has_change_permission(request):
            changelist.title = str(self.model._meta.verbose_name_plural)
        return changelist

    def changelist_view(self, request, extra_context=None):
        context = dict(extra_context or {})
        if not self.has_change_permission(request):
            # Django builds "Select %s to view" for read-only models. Use the
            # plain model label in both the page heading and browser tab title.
            context["title"] = str(self.model._meta.verbose_name_plural)
        context.update(self._calendar_context(request))
        return super().changelist_view(request, extra_context=context)


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
        help_text="사진 파일 첨부는 아래 ‘매장 사진’에서 가능합니다. 권장 1200×900px(4:3), 최소 800×600px. 주소가 있는 대표 사진만 입력하세요.")
    representative_photo_url = forms.URLField(label="대표자 사진 주소", required=False,
        help_text="권장 800×800px(1:1) 정사각형, 최소 400×400px. 얼굴이 중앙에 오도록 준비해 주세요.")
    service_categories = forms.MultipleChoiceField(
        label="서비스 분야",
        required=False,
        help_text="분야를 선택하세요. 아래 ‘+ 분야 추가’에서 새 선택 항목을 등록할 수 있습니다.",
        widget=forms.CheckboxSelectMultiple(attrs={"class": "partner-service-categories"}),
    )

    class Meta:
        model = Partner
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        existing = self.initial.get("service_categories", [])
        options = list(PartnerServiceCategoryOption.objects.filter(is_active=True).values_list("name", flat=True))
        if isinstance(existing, list):
            options = list(dict.fromkeys([*options, *existing]))
            self.fields["service_categories"].initial = existing
        self.fields["service_categories"].choices = [(name, name) for name in options]

    def clean_service_categories(self):
        return list(dict.fromkeys(self.cleaned_data["service_categories"]))

    class Media:
        js = ("core/partner_service_categories.js",)


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
class VehicleAdmin(AdminCalendarMixin, admin.ModelAdmin):
    list_display = ("id", "current_owner", "model_name", "plate_number", "model_year", "current_odometer_km", "public_id", "created_at")
    list_filter = ("model_year",)
    search_fields = ("ownerships__user__username", "ownerships__user__email", "model_name", "nickname", "generation", "plate_number", "vin_hash")
    readonly_fields = ("public_id", "created_at")
    date_hierarchy = "created_at"

    @admin.display(description="현재 등록 사용자")
    def current_owner(self, obj):
        owner = obj.owner
        return member_nickname(owner) if owner else "미지정"

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop("delete_selected", None)
        return actions

    def has_delete_permission(self, request, obj=None):
        if obj and obj.ledger_entries.filter(source=LedgerEntry.Source.PARTNER).exists():
            return False
        return super().has_delete_permission(request, obj)


@admin.register(VehiclePlateHistory)
class VehiclePlateHistoryAdmin(AdminCalendarMixin, admin.ModelAdmin):
    list_display = ("vehicle", "plate_number", "started_at", "ended_at", "changed_by_nickname")
    search_fields = ("plate_number", "vehicle__model_name", "changed_by__username", "changed_by__naver_identity__cafe_nickname", "changed_by__apple_identity__cafe_nickname")
    readonly_fields = tuple(field.name for field in VehiclePlateHistory._meta.fields)
    date_hierarchy = "started_at"

    @admin.display(description="변경 담당자")
    def changed_by_nickname(self, obj):
        return member_nickname(obj.changed_by) if obj.changed_by else "—"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop("delete_selected", None)
        return actions


@admin.register(VehicleOwnership)
class VehicleOwnershipAdmin(AdminCalendarMixin, admin.ModelAdmin):
    list_display = ("vehicle", "member_nickname", "relationship", "started_at", "ended_at", "verification_method", "verification_status")
    list_filter = ("relationship", "verification_status", "verification_method")
    search_fields = ("vehicle__model_name", "user__username", "user__email", "user__naver_identity__cafe_nickname", "user__apple_identity__cafe_nickname")
    readonly_fields = tuple(field.name for field in VehicleOwnership._meta.fields)
    date_hierarchy = "started_at"

    @admin.display(description="회원 닉네임")
    def member_nickname(self, obj):
        return member_nickname(obj.user)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(LedgerEntry)
class LedgerEntryAdmin(AdminCalendarMixin, admin.ModelAdmin):
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
class ReminderAdmin(AdminCalendarMixin, admin.ModelAdmin):
    list_display = ("title", "vehicle", "due_date", "due_odometer_km", "completed_at", "notification_sent_at")
    list_filter = ("completed_at", "due_date")
    search_fields = ("title", "vehicle__model_name", "vehicle__nickname")
    date_hierarchy = "created_at"
    readonly_fields = ("created_at", "notification_sent_at")


@admin.register(AttendanceCheckin)
class AttendanceCheckinAdmin(AdminCalendarMixin, admin.ModelAdmin):
    list_display = ("checkin_date", "member", "points_awarded", "created_at")
    list_filter = ("checkin_date",)
    search_fields = ("user__username", "user__email", "user__naver_identity__nickname", "user__naver_identity__cafe_nickname", "user__apple_identity__cafe_nickname")
    list_select_related = ("user__naver_identity", "user__apple_identity")
    readonly_fields = tuple(field.name for field in AttendanceCheckin._meta.fields)
    date_hierarchy = "checkin_date"

    @admin.display(description="회원")
    def member(self, obj):
        return member_nickname(obj.user)

    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False


@admin.register(PointTransaction)
class PointTransactionAdmin(AdminCalendarMixin, admin.ModelAdmin):
    list_display = ("created_at", "member", "transaction_type", "points_delta", "partner_detail", "ledger_detail", "memo")
    list_display_links = ("created_at",)
    list_filter = ("transaction_type", "created_at", "partner")
    search_fields = ("user__username", "user__email", "user__naver_identity__nickname", "user__naver_identity__cafe_nickname", "user__apple_identity__cafe_nickname", "memo", "idempotency_key")
    list_select_related = ("user__naver_identity", "user__apple_identity", "partner", "ledger_entry__vehicle")
    readonly_fields = (
        "member_detail", "transaction_type", "points_delta", "created_at", "available_at",
        "partner_detail", "ledger_detail", "redemption_details", "memo", "idempotency_key",
    )
    fieldsets = (
        ("회원", {"fields": ("member_detail",)}),
        ("포인트 거래", {"fields": ("transaction_type", "points_delta", "created_at", "available_at", "memo")}),
        ("사용처 및 연결 기록", {"fields": ("partner_detail", "ledger_detail", "redemption_details")}),
        ("시스템 정보", {"fields": ("idempotency_key",)}),
    )
    list_per_page = 50
    date_hierarchy = "created_at"

    @admin.display(description="회원 닉네임 / 식별번호")
    def member(self, obj):
        return format_html(
            '<a href="{}">{} · 회원 #{}</a>',
            reverse("admin:auth_user_change", args=[obj.user_id]),
            member_nickname(obj.user), obj.user_id,
        )

    @admin.display(description="회원 닉네임 / 식별번호", ordering="user_id")
    def member_detail(self, obj):
        return self.member(obj)

    @admin.display(description="사용 업체")
    def partner_detail(self, obj):
        if not obj.partner_id:
            return "업체 거래 아님"
        return format_html(
            '<a href="{}">{}{}</a>',
            reverse("admin:core_partner_change", args=[obj.partner_id]),
            obj.partner.name,
            f" · {obj.partner.branch_label}" if obj.partner.branch_label else "",
        )

    @admin.display(description="연결된 차계부 / 정비 기록")
    def ledger_detail(self, obj):
        entry = obj.ledger_entry
        if not entry:
            return "연결된 정비 기록 없음"
        vehicle = entry.vehicle
        title = f"{entry.entry_date:%Y-%m-%d} · {vehicle.plate_number or '번호 미등록'} · {entry.get_kind_display()}"
        odometer = f"{entry.odometer_km:,}" if entry.odometer_km is not None else "주행거리 미등록"
        amount = f"{entry.amount_krw:,}"
        return format_html(
            '<a href="{}">{} · {}원 · {}km</a>',
            reverse("admin:core_ledgerentry_change", args=[entry.pk]),
            title, amount, odometer,
        )

    @admin.display(description="포인트 사용 요청 상세")
    def redemption_details(self, obj):
        requests = list(obj.redemption_requests.select_related("partner").order_by("-created_at"))
        if not requests:
            return "연결된 포인트 사용 요청 없음"
        lines = []
        for point_request in requests:
            completed = point_request.completed_at.strftime("%Y-%m-%d %H:%M:%S") if point_request.completed_at else "미완료"
            label = (
                f"{point_request.partner.name} · {point_request.get_status_display()} · "
                f"요청 {point_request.points_requested:,}P · 결제 {point_request.payment_amount_krw:,}원 · "
                f"요청 {point_request.created_at:%Y-%m-%d %H:%M:%S} · 완료 {completed}"
            )
            lines.append(format_html(
                '<a href="{}">{}</a>',
                reverse("admin:core_pointredemptionrequest_change", args=[point_request.pk]), label,
            ))
        return format_html("<br>".join("{}" for _ in lines), *lines)

    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False


@admin.register(PointRedemptionRequest)
class PointRedemptionRequestAdmin(AdminCalendarMixin, admin.ModelAdmin):
    list_display = ("created_at", "member_nickname", "partner", "payment_amount_krw", "points_requested", "status", "expires_at", "responded_at", "completed_at")
    list_filter = ("status", "created_at", "partner")
    search_fields = ("member__username", "member__email", "member__naver_identity__nickname", "member__naver_identity__cafe_nickname", "member__apple_identity__cafe_nickname", "partner__name", "partner__branch_label")
    list_select_related = ("member__naver_identity", "member__apple_identity", "partner", "transaction")
    readonly_fields = tuple(field.name for field in PointRedemptionRequest._meta.fields)
    date_hierarchy = "created_at"

    @admin.display(description="회원")
    def member_nickname(self, obj):
        return member_nickname(obj.member)

    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False


class OfferInline(admin.TabularInline):
    model = Offer
    form = OfferAdminForm
    extra = 0
    fields = ("title", "is_active", "starts_at", "ends_at", "description", "redemption_instructions")


@admin.register(Notice)
class NoticeAdmin(AdminCalendarMixin, admin.ModelAdmin):
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
        help_text="권장 1200×900px(4:3), 최소 800×600px. PNG, JPEG, WebP 파일, 최대 5MB. 기존 이미지를 바꾸려면 새 파일을 선택하세요.",
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
            if data.startswith(b"\x89PNG\r\n\x1a\n"):
                mime = "image/png"
            elif data.startswith(b"\xff\xd8\xff"):
                mime = "image/jpeg"
            elif data[:4] == b"RIFF" and data[8:12] == b"WEBP":
                mime = "image/webp"
            if not mime:
                self.add_error("upload", "PNG, JPEG, WebP 이미지 파일만 첨부할 수 있습니다.")
            else:
                self.instance.image_data = data
                self.instance.content_type = mime
        elif not self.instance.pk:
            self.add_error("upload", "소개 이미지 파일을 첨부해 주세요.")
        return cleaned


class PartnerImageInline(admin.TabularInline):
    model = PartnerImage
    form = PartnerImageAdminForm
    fields = ("preview", "upload", "caption", "display_order")
    readonly_fields = ("preview",)
    extra = 1
    verbose_name = "매장 사진"
    verbose_name_plural = "매장 사진 · 파일 첨부 및 교체"

    @admin.display(description="현재 이미지")
    def preview(self, obj):
        if not obj.pk:
            return "저장 후 표시됩니다."
        return format_html('<img src="/api/partners/{}/images/{}/" style="max-width:180px;max-height:120px" alt="업체 소개 이미지">', obj.partner_id, obj.pk)


@admin.register(PartnerImage)
class PartnerImageAdmin(AdminCalendarMixin, admin.ModelAdmin):
    form = PartnerImageAdminForm
    list_display = ("partner", "caption", "display_order")
    list_filter = ("partner",)
    fields = ("partner", "upload", "caption", "display_order")


@admin.register(Partner)
class PartnerAdmin(AdminCalendarMixin, admin.ModelAdmin):
    form = PartnerAdminForm
    list_display = ("name", "branch_label", "region", "is_active", "is_sponsored", "display_order")
    list_editable = ("is_active", "is_sponsored", "display_order")
    list_filter = ("is_active", "is_sponsored", "region")
    search_fields = ("name", "branch_label", "region", "description", "address")
    save_on_top = True
    inlines = (PartnerImageInline, OfferInline)
    fieldsets = (
        ("업체 기본 정보", {"fields": ("name", "branch_label", "region", "service_categories")}),
        ("업체 소개 글", {"description": "앱의 사진 아래 소개 문구를 수정하는 곳입니다.", "fields": ("description",)}),
        ("매장 상세 안내", {"description": "앱의 업체 정보에 표시할 방문 및 이용 안내입니다.", "fields": ("business_info",)}),
        ("대표 사진 주소", {"description": "파일 사진은 아래 매장 사진에서 첨부하세요. 이 항목은 외부 이미지 주소가 있을 때만 사용합니다.", "fields": ("storefront_photo_url",)}),
        ("대표 정비사", {"fields": ("representative_name", "representative_title", "representative_experience_years", "representative_photo_url")}),
        ("연락처 및 연결", {"fields": ("address", "phone", "hours", "cafe_url", "map_url")}),
        ("앱 노출 설정", {"fields": ("is_active", "is_sponsored", "display_order")}),
    )

    def get_urls(self):
        custom = [
            path(
                "add-service-category/",
                self.admin_site.admin_view(self.add_service_category),
                name="core_partner_add_service_category",
            ),
        ]
        return custom + super().get_urls()

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields["service_categories"].widget.attrs["data-add-url"] = reverse(
            "admin:core_partner_add_service_category"
        )
        return form

    def add_service_category(self, request):
        if request.method != "POST" or not self.has_change_permission(request):
            return JsonResponse({"detail": "권한이 없거나 요청 방식이 올바르지 않습니다."}, status=403)
        name = " ".join(request.POST.get("name", "").split())
        if not name or len(name) > 80:
            return JsonResponse({"detail": "서비스 분야를 1~80자로 입력해 주세요."}, status=400)
        option, _ = PartnerServiceCategoryOption.objects.get_or_create(
            name=name, defaults={"display_order": 100}
        )
        if not option.is_active:
            option.is_active = True
            option.save(update_fields=["is_active"])
        return JsonResponse({"value": option.name, "label": option.name})


@admin.register(PartnerServiceCategoryOption)
class PartnerServiceCategoryOptionAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "display_order")
    list_editable = ("is_active", "display_order")
    search_fields = ("name",)
    ordering = ("display_order", "name")


@admin.register(PartnerReview)
class PartnerReviewAdmin(AdminCalendarMixin, admin.ModelAdmin):
    list_display = ("partner", "reviewer_nickname", "rating", "created_at", "updated_at")
    list_filter = ("rating", "created_at")
    search_fields = ("partner__name", "partner__branch_label", "comment", "user__naver_identity__nickname", "user__naver_identity__cafe_nickname", "user__apple_identity__cafe_nickname")
    readonly_fields = ("created_at", "updated_at")

    @admin.display(description="회원 닉네임")
    def reviewer_nickname(self, obj):
        return member_nickname(obj.user)
    date_hierarchy = "created_at"


@admin.register(PartnerStaff)
class PartnerStaffAdmin(AdminCalendarMixin, admin.ModelAdmin):
    autocomplete_fields = ("user",)

    def get_urls(self):
        return [path("member-autocomplete/", self.admin_site.admin_view(MemberAutocompleteView.as_view(admin_site=self.admin_site)), name="core_partnerstaff_member_autocomplete")] + super().get_urls()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "user":
            kwargs["widget"] = MemberAutocompleteSelect(db_field.remote_field, self.admin_site)
            kwargs["queryset"] = db_field.remote_field.model.objects.select_related("naver_identity", "apple_identity")
            field = super().formfield_for_foreignkey(db_field, request, **kwargs)
            field.label_from_instance = member_label
            return field
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    @admin.display(description="회원 닉네임")
    def member_account(self, obj):
        return member_nickname(obj.user)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user__naver_identity", "user__apple_identity", "partner")
    list_display = ("member_account", "partner", "can_verify_records", "can_manage_bookings", "is_active", "created_at")
    list_editable = ("can_verify_records", "can_manage_bookings", "is_active")
    list_filter = ("partner", "can_verify_records", "can_manage_bookings", "is_active")
    search_fields = ("user__username", "user__email", "user__naver_identity__nickname", "user__naver_identity__cafe_nickname", "user__apple_identity__cafe_nickname", "=user__id", "partner__name")
    readonly_fields = ("created_at",)
    date_hierarchy = "created_at"


@admin.register(Offer)
class OfferAdmin(AdminCalendarMixin, admin.ModelAdmin):
    form = OfferAdminForm
    list_display = ("title", "partner", "is_active", "starts_at", "ends_at")
    list_editable = ("is_active",)
    list_filter = ("is_active", "partner")
    search_fields = ("title", "description", "partner__name")
    date_hierarchy = "starts_at"
    save_on_top = True


@admin.register(PushDevice)
class PushDeviceAdmin(AdminCalendarMixin, admin.ModelAdmin):
    list_display = ("member_nickname", "platform", "updated_at")
    list_filter = ("platform",)
    search_fields = ("user__username", "user__email", "user__naver_identity__cafe_nickname", "user__apple_identity__cafe_nickname", "installation_id")
    readonly_fields = ("user", "installation_id", "platform", "created_at", "updated_at")
    date_hierarchy = "updated_at"

    @admin.display(description="회원 닉네임")
    def member_nickname(self, obj):
        return member_nickname(obj.user)

    def has_add_permission(self, request):
        return False


@admin.register(VehicleTransferCode)
class VehicleTransferCodeAdmin(AdminCalendarMixin, admin.ModelAdmin):
    list_display = ("vehicle", "previous_owner_nickname", "new_owner_nickname", "created_at", "expires_at", "accepted_at", "invalidated_at")
    list_filter = ("accepted_at", "invalidated_at", "created_at")
    search_fields = ("vehicle__model_name", "previous_owner__username", "previous_owner__naver_identity__cafe_nickname", "previous_owner__apple_identity__cafe_nickname", "new_owner__username", "new_owner__naver_identity__cafe_nickname", "new_owner__apple_identity__cafe_nickname")
    readonly_fields = tuple(field.name for field in VehicleTransferCode._meta.fields if field.name != "code_digest")
    exclude = ("code_digest",)
    date_hierarchy = "created_at"

    @admin.display(description="이전 소유자 닉네임")
    def previous_owner_nickname(self, obj):
        return member_nickname(obj.previous_owner) if obj.previous_owner else "—"

    @admin.display(description="새 소유자 닉네임")
    def new_owner_nickname(self, obj):
        return member_nickname(obj.new_owner) if obj.new_owner else "—"

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


class AppleProfileInline(admin.StackedInline):
    model = AppleIdentity
    verbose_name = "Apple 로그인 정보"
    verbose_name_plural = "Apple 로그인 정보"
    fields = ("cafe_nickname", "email", "subject", "created_at")
    readonly_fields = fields
    extra = 0
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        return bool(request.user.is_active and request.user.is_superuser)


class MemberPointTransactionInline(admin.TabularInline):
    model = PointTransaction
    verbose_name = "포인트 거래"
    verbose_name_plural = "전체 포인트 거래 내역"
    fk_name = "user"
    fields = ("created_at", "transaction_type", "points_delta", "partner", "ledger_entry", "memo")
    readonly_fields = fields
    ordering = ("-created_at", "-pk")
    extra = 0
    can_delete = False
    show_change_link = True

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("partner", "ledger_entry")

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        return bool(request.user.is_active and request.user.is_superuser)


User = get_user_model()
admin.site.unregister(User)


@admin.register(User)
class MemberUserAdmin(AdminCalendarMixin, UserAdmin):
    inlines = (NaverProfileInline, AppleProfileInline, MemberPointTransactionInline)
    list_display = ("id", "display_nickname", "display_member_name", "email", "display_mobile", "ilovemini_grade", "display_points_balance", "display_workplaces", "is_active", "date_joined", "last_login")
    search_fields = ("naver_identity__nickname", "naver_identity__cafe_nickname", "apple_identity__cafe_nickname", "email", "username", "first_name", "last_name", "naver_identity__mobile", "=id")
    list_per_page = 50
    date_hierarchy = "date_joined"
    ordering = ("-date_joined", "-id")
    list_filter = ("is_active", "is_staff", "is_superuser", "groups")
    readonly_fields = (*UserAdmin.readonly_fields, "display_nickname", "id", "display_workplaces", "display_points_earned", "display_points_used", "display_points_balance")
    fieldsets = (
        ("회원 식별 정보", {"fields": ("id", "display_nickname", "display_workplaces")}),
        ("포인트 요약", {"fields": ("display_points_earned", "display_points_used", "display_points_balance")}),
    ) + UserAdmin.fieldsets

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
        point_total = PointTransaction.objects.filter(user_id=OuterRef("pk")).order_by().values("user_id").annotate(total=Sum("points_delta")).values("total")[:1]
        return (super().get_queryset(request).select_related("naver_identity", "apple_identity")
                .prefetch_related("partner_memberships__partner", "groups")
                .annotate(_point_balance=Coalesce(Subquery(point_total, output_field=IntegerField()), Value(0))))
    actions = [grade_action(code) for code in GRADES] + ["export_members_csv"]

    @admin.display(description="소속 협력업체")
    def display_workplaces(self, obj):
        names = [staff.partner.name for staff in obj.partner_memberships.all() if staff.is_active and staff.partner.is_active]
        return " / ".join(names) or "—"

    @admin.display(description="포인트 잔액", ordering="_point_balance")
    def display_points_balance(self, obj):
        balance = getattr(obj, "_point_balance", None)
        if balance is None:
            balance = obj.point_transactions.aggregate(total=Sum("points_delta"))["total"] or 0
        return f"{balance:,}P"

    @admin.display(description="누적 적립")
    def display_points_earned(self, obj):
        total = obj.point_transactions.filter(points_delta__gt=0).aggregate(total=Sum("points_delta"))["total"] or 0
        return f"{total:,}P"

    @admin.display(description="누적 사용")
    def display_points_used(self, obj):
        total = obj.point_transactions.filter(points_delta__lt=0).aggregate(total=Sum("points_delta"))["total"] or 0
        return f"{abs(total):,}P"

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

class SeasonBannerAdminForm(forms.ModelForm):
    class Meta:
        model = SeasonBanner
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["image_url"].help_text = (
            "앱 시작 시즌 배너용 권장 1080×1920px(9:16 세로형). "
            "제목·중요 문구는 가장자리에서 10% 안쪽에 배치하세요. 공개 HTTPS 이미지 주소를 입력합니다."
        )


@admin.register(SeasonBanner)
class SeasonBannerAdmin(AdminCalendarMixin, admin.ModelAdmin):
    form = SeasonBannerAdminForm
    list_display = ("title", "is_active", "starts_at", "ends_at", "duration_seconds", "priority")
    list_editable = ("is_active", "priority")
    list_filter = ("is_active",)
    search_fields = ("title", "subtitle")
    date_hierarchy = "starts_at"
    save_on_top = True

class AppContentAdminForm(forms.ModelForm):
    class Meta:
        model = AppContent
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["image_url"].help_text = (
            "권장 1200×1200px(1:1 정사각형), 최소 800×800px. "
            "앱 카드에서 잘리지 않도록 주요 피사체를 중앙에 두세요. 공개 HTTPS 이미지 주소를 입력합니다."
        )


@admin.register(AppContent)
class AppContentAdmin(AdminCalendarMixin, admin.ModelAdmin):
    form = AppContentAdminForm
    list_display = ("title", "kind", "category", "is_active", "display_order", "starts_at", "ends_at")
    list_editable = ("is_active", "display_order")
    list_filter = ("kind", "category", "is_active")
    search_fields = ("title", "description", "compatible_models")
    date_hierarchy = "starts_at"
    save_on_top = True

@admin.register(AppRelease)
class AppReleaseAdmin(AdminCalendarMixin, admin.ModelAdmin):
    list_display = ("platform", "version", "build_number", "is_active")
    list_editable = ("is_active",)
    search_fields = ("version", "notes")
    save_on_top = True

class PrimaryVehicleAssignedFilter(admin.SimpleListFilter):
    title = "대표 차량 설정"
    parameter_name = "vehicle_assigned"

    def lookups(self, request, model_admin):
        return (("assigned", "설정됨"), ("unassigned", "미설정"))

    def queryset(self, request, queryset):
        if self.value() == "assigned":
            return queryset.filter(primary_vehicle__isnull=False)
        if self.value() == "unassigned":
            return queryset.filter(primary_vehicle__isnull=True)
        return queryset


class MemberPreferenceAdminForm(forms.ModelForm):
    class Meta:
        model = MemberPreference
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user_id = self.data.get("user") or self.initial.get("user") or getattr(self.instance, "user_id", None)
        vehicle_field = self.fields["primary_vehicle"]
        vehicle_field.queryset = Vehicle.objects.filter(
            status="active", ownerships__user_id=user_id, ownerships__ended_at__isnull=True,
        ).distinct() if user_id else Vehicle.objects.none()

        def vehicle_label(vehicle):
            plate = vehicle.plate_number or "번호 미등록"
            return f"{plate} · {vehicle.model_name}"

        vehicle_field.label_from_instance = vehicle_label


@admin.register(MemberPreference)
class MemberPreferenceAdmin(AdminCalendarMixin, admin.ModelAdmin):
    form = MemberPreferenceAdminForm
    list_display = ("member", "member_number", "primary_vehicle")
    list_filter = (PrimaryVehicleAssignedFilter,)
    search_fields = (
        "user__naver_identity__cafe_nickname", "user__naver_identity__nickname",
        "user__apple_identity__cafe_nickname", "user__username", "=user__id",
        "primary_vehicle__plate_number", "primary_vehicle__model_name",
    )
    list_select_related = ("user__naver_identity", "user__apple_identity", "primary_vehicle")
    readonly_fields = ("user",)
    list_per_page = 50

    @admin.display(description="회원 닉네임")
    def member(self, obj):
        return member_nickname(obj.user)

    @admin.display(description="회원번호", ordering="user_id")
    def member_number(self, obj):
        return f"#{obj.user_id}"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
@admin.register(RecordCorrectionRequest)
class RecordCorrectionRequestAdmin(AdminCalendarMixin, admin.ModelAdmin):
    list_display = ("entry", "member", "reason", "created_at", "resolved_at")
    list_select_related = ("requested_by__naver_identity", "requested_by__apple_identity", "entry")
    list_filter = ("resolved_at",)
    date_hierarchy = "created_at"
    readonly_fields = ("entry", "requested_by", "reason", "created_at", "resolved_entry", "resolved_at")
    @admin.display(description="요청 회원")
    def member(self, obj): return member_nickname(obj.requested_by)
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False


# Register app review account management after the core admin models.
from . import review_admin as _review_admin
