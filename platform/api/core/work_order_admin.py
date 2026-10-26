from django import forms
from django.contrib import admin
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from .member_display import member_nickname
from .models import PartnerBooking, PartnerStaff, PartnerWorkOrder
from .phase_one_admin import EstimateItemsWidget


class PartnerWorkOrderForm(forms.ModelForm):
    class Meta:
        model = PartnerWorkOrder
        fields = (
            "partner", "booking", "customer_name", "contact_phone", "vehicle_model",
            "plate_number", "odometer_km", "customer_concern", "inspection_notes",
            "items", "quoted_total_krw", "final_total_krw", "paid_amount_krw",
            "payment_method", "status", "technician_name", "work_notes",
            "customer_message", "internal_note",
        )
        widgets = {"items": EstimateItemsWidget}

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        staff = PartnerStaff.objects.filter(
            user=request.user, is_active=True, can_manage_bookings=True, partner__is_active=True
        ) if request and request.user.is_authenticated else PartnerStaff.objects.none()
        partner_ids = staff.values_list("partner_id", flat=True)
        self.fields["partner"].queryset = self.fields["partner"].queryset.filter(pk__in=partner_ids)
        self.fields["booking"].queryset = PartnerBooking.objects.filter(partner_id__in=partner_ids).select_related(
            "partner", "vehicle", "customer__naver_identity", "customer__apple_identity"
        )
        if self.instance.pk:
            self.fields["partner"].disabled = True
            self.fields["booking"].disabled = True

    def clean_items(self):
        items = self.cleaned_data.get("items") or []
        if not isinstance(items, list) or len(items) > 50:
            raise ValidationError("부품·공임 항목은 50개 이하로 입력해 주세요.")
        cleaned = []
        for item in items:
            if not isinstance(item, dict):
                raise ValidationError("각 항목의 형식이 올바르지 않습니다.")
            title, amount = item.get("title"), item.get("amount_krw")
            if not isinstance(title, str) or not title.strip() or len(title.strip()) > 160:
                raise ValidationError("각 항목의 작업명 또는 부품명을 입력해 주세요.")
            if type(amount) is not int or not 0 <= amount <= 100_000_000:
                raise ValidationError("항목별 금액은 0원 이상 1억원 이하로 입력해 주세요.")
            cleaned.append({"title": title.strip(), "amount_krw": amount})
        return cleaned

    def clean(self):
        data = super().clean()
        booking = data.get("booking")
        partner = data.get("partner") or getattr(self.instance, "partner", None)
        if booking and partner and booking.partner_id != partner.pk:
            self.add_error("booking", "선택한 예약과 협력업체가 일치하지 않습니다.")
        if data.get("paid_amount_krw", 0) > data.get("final_total_krw", 0):
            self.add_error("paid_amount_krw", "수납 금액이 최종 정비 금액보다 클 수 없습니다.")
        if data.get("status") == PartnerWorkOrder.Status.COMPLETED and data.get("final_total_krw", 0) < 0:
            self.add_error("final_total_krw", "정비 완료 금액을 확인해 주세요.")
        return data


class PartnerWorkOrderAdmin(admin.ModelAdmin):
    form = PartnerWorkOrderForm
    list_display = (
        "order_number", "created_at", "customer_name", "vehicle_summary",
        "contact_phone", "status", "quoted_total_krw", "paid_amount_krw",
    )
    list_filter = ("status", "created_at")
    search_fields = ("customer_name", "contact_phone", "plate_number", "vehicle_model", "customer_concern")
    list_select_related = ("partner", "booking", "created_by")
    ordering = ("-created_at", "-pk")
    actions = None
    fieldsets = (
        ("접수 정보", {"fields": ("partner", "booking", ("customer_name", "contact_phone"), ("vehicle_model", "plate_number", "odometer_km"), "customer_concern", "status")}),
        ("점검·작업", {"fields": ("inspection_notes", "items", ("quoted_total_krw", "final_total_krw"), ("technician_name", "work_notes"), "customer_message")}),
        ("수납", {"fields": (("paid_amount_krw", "payment_method"),)}),
        ("업체 메모", {"fields": ("internal_note",)}),
        ("기록", {"fields": ("created_by", "created_at", "updated_at", "completed_at"), "classes": ("collapse",)}),
    )
    readonly_fields = ("created_by", "created_at", "updated_at", "completed_at")

    class Media:
        css = {"all": ("core/partner_admin.css",)}

    @admin.display(description="작업 번호", ordering="pk")
    def order_number(self, obj):
        return f"WO-{obj.created_at:%y%m%d}-{obj.pk:05d}"

    @admin.display(description="차량")
    def vehicle_summary(self, obj):
        return " · ".join(value for value in (obj.plate_number, obj.vehicle_model) if value) or "차량 미입력"

    def get_queryset(self, request):
        return super().get_queryset(request).filter(
            partner_id__in=PartnerStaff.objects.filter(
                user=request.user, is_active=True, can_manage_bookings=True, partner__is_active=True
            ).values_list("partner_id", flat=True)
        ).select_related("partner", "booking", "created_by")

    def get_form(self, request, obj=None, **kwargs):
        base = super().get_form(request, obj, **kwargs)
        class RequestForm(base):
            def __init__(self, *args, **form_kwargs):
                form_kwargs["request"] = request
                super().__init__(*args, **form_kwargs)
        return RequestForm

    def has_module_permission(self, request):
        return PartnerStaff.objects.filter(
            user=request.user, is_active=True, can_manage_bookings=True, partner__is_active=True
        ).exists()

    def has_view_permission(self, request, obj=None):
        allowed = self.has_module_permission(request)
        return allowed and (obj is None or obj.partner_id in PartnerStaff.objects.filter(
            user=request.user, is_active=True, can_manage_bookings=True, partner__is_active=True
        ).values_list("partner_id", flat=True))

    def has_add_permission(self, request):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_view_permission(request, obj) and (
            obj is None or obj.status != PartnerWorkOrder.Status.COMPLETED
        )

    def has_delete_permission(self, request, obj=None):
        return False

    @transaction.atomic
    def save_model(self, request, obj, form, change):
        partner_ids = list(PartnerStaff.objects.filter(
            user=request.user, is_active=True, can_manage_bookings=True, partner__is_active=True
        ).values_list("partner_id", flat=True))
        if obj.partner_id not in partner_ids:
            raise PermissionDenied("담당 협력업체의 작업만 저장할 수 있습니다.")
        if change and not PartnerWorkOrder.objects.filter(pk=obj.pk, partner_id__in=partner_ids).exists():
            raise PermissionDenied("해당 작업에 접근할 수 없습니다.")
        booking = form.cleaned_data.get("booking")
        if booking:
            if booking.partner_id != obj.partner_id:
                raise PermissionDenied("예약과 업체가 일치하지 않습니다.")
            obj.vehicle = booking.vehicle
            if not obj.customer_name:
                obj.customer_name = member_nickname(booking.customer)
            if not obj.contact_phone:
                obj.contact_phone = booking.contact_phone
            if booking.vehicle:
                obj.vehicle_model = obj.vehicle_model or booking.vehicle.model_name
                obj.plate_number = obj.plate_number or booking.vehicle.plate_number
                obj.odometer_km = obj.odometer_km or booking.vehicle.current_odometer_km
        if not change:
            obj.created_by = request.user
        items = form.cleaned_data.get("items") or []
        if items and not obj.quoted_total_krw:
            obj.quoted_total_krw = sum(row["amount_krw"] for row in items)
        if obj.status == PartnerWorkOrder.Status.COMPLETED and not obj.completed_at:
            obj.completed_at = timezone.now()
        super().save_model(request, obj, form, change)

