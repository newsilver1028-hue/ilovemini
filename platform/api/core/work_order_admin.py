from django import forms
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import F
from django.urls import reverse
from django.utils.html import format_html
from django.utils import timezone

from .member_display import member_nickname
from .models import PartnerBooking, PartnerStaff, PartnerWorkOrder, Partner, PartnerCustomer, PartnerVehicle, PartnerPart, PartnerWorkOrderLine, PartnerStockMovement, PartnerPayment, PartnerServicePreset, PartnerWorkResource, PartnerQuoteShare
from .partner_admin import is_system_admin, staff_partners


class PartnerWorkOrderForm(forms.ModelForm):
    class Meta:
        model = PartnerWorkOrder
        fields = (
            "partner", "booking", "customer_name", "contact_phone", "vehicle_model",
            "customer", "partner_vehicle",
            "plate_number", "odometer_km", "customer_concern", "inspection_notes",
            "quoted_total_krw", "quote_status", "quote_revision", "quote_responded_at", "quote_decline_reason", "final_total_krw", "paid_amount_krw",
            "payment_method", "status", "technician_name", "assigned_resource", "work_notes",
            "customer_message", "internal_note",
        )

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        if request and is_system_admin(request):
            partner_ids = Partner.objects.filter(is_active=True).values_list("id", flat=True)
        else:
            staff = PartnerStaff.objects.filter(
                user=request.user, is_active=True, can_manage_bookings=True, partner__is_active=True
            ) if request and request.user.is_authenticated else PartnerStaff.objects.none()
            partner_ids = staff.values_list("partner_id", flat=True)
        self.fields["partner"].queryset = self.fields["partner"].queryset.filter(pk__in=partner_ids)
        self.fields["booking"].queryset = PartnerBooking.objects.filter(partner_id__in=partner_ids).select_related(
            "partner", "vehicle", "customer__naver_identity", "customer__apple_identity"
        )
        self.fields["customer"].queryset = PartnerCustomer.objects.filter(partner_id__in=partner_ids, is_active=True)
        self.fields["partner_vehicle"].queryset = PartnerVehicle.objects.filter(partner_id__in=partner_ids, is_active=True).select_related("customer")
        self.fields["assigned_resource"].queryset = PartnerWorkResource.objects.filter(partner_id__in=partner_ids, is_active=True)
        self.fields["quote_status"].disabled = True
        self.fields["quote_revision"].disabled = True
        self.fields["quote_responded_at"].disabled = True
        self.fields["quote_decline_reason"].disabled = True
        if self.instance.pk:
            self.fields["partner"].disabled = True
            self.fields["booking"].disabled = True

    def clean(self):
        data = super().clean()
        booking = data.get("booking")
        partner = data.get("partner") or getattr(self.instance, "partner", None)
        if booking and partner and booking.partner_id != partner.pk:
            self.add_error("booking", "선택한 예약과 협력업체가 일치하지 않습니다.")
        customer, partner_vehicle = data.get("customer"), data.get("partner_vehicle")
        if customer and partner and customer.partner_id != partner.pk:
            self.add_error("customer", "고객 대장과 협력업체가 일치하지 않습니다.")
        if partner_vehicle and partner and partner_vehicle.partner_id != partner.pk:
            self.add_error("partner_vehicle", "차량 대장과 협력업체가 일치하지 않습니다.")
        assigned_resource = data.get("assigned_resource")
        if assigned_resource and partner and assigned_resource.partner_id != partner.pk:
            self.add_error("assigned_resource", "담당 정비사·작업대가 협력업체와 일치하지 않습니다.")
        if customer and partner_vehicle and customer.pk != partner_vehicle.customer_id:
            self.add_error("partner_vehicle", "차량 대장의 고객을 확인해 주세요.")
        if data.get("paid_amount_krw", 0) > data.get("final_total_krw", 0):
            self.add_error("paid_amount_krw", "수납 금액이 최종 정비 금액보다 클 수 없습니다.")
        if data.get("status") == PartnerWorkOrder.Status.COMPLETED and data.get("final_total_krw", 0) < 0:
            self.add_error("final_total_krw", "정비 완료 금액을 확인해 주세요.")
        return data


class PartnerWorkOrderAdmin(admin.ModelAdmin):
    form = PartnerWorkOrderForm
    change_form_template = "admin/core/partnerworkorder/change_form.html"
    list_display = (
        "order_number", "created_at", "customer_name", "vehicle_summary",
        "contact_phone", "status", "quoted_total_krw", "paid_amount_krw", "quote_print_link",
    )
    list_filter = ("status", "created_at")
    search_fields = ("customer_name", "contact_phone", "plate_number", "vehicle_model", "customer_concern")
    list_select_related = ("partner", "booking", "created_by")
    ordering = ("-created_at", "-pk")
    actions = None
    fieldsets = (
        ("접수 정보", {"fields": ("partner", "booking", ("customer", "partner_vehicle"), ("customer_name", "contact_phone"), ("vehicle_model", "plate_number", "odometer_km"), "customer_concern", "status")}),
        ("점검·작업", {"fields": ("inspection_notes", ("quoted_total_krw", "quote_status", "quote_revision"), ("quote_responded_at", "quote_decline_reason"), "final_total_krw", ("technician_name", "assigned_resource"), "work_notes", "customer_message")}),
        ("수납", {"fields": (("paid_amount_krw", "payment_method"),)}),
        ("업체 메모", {"fields": ("internal_note",)}),
        ("기록", {"fields": ("created_by", "created_at", "updated_at", "completed_at"), "classes": ("collapse",)}),
    )
    readonly_fields = ("created_by", "created_at", "updated_at", "completed_at")
    inlines = []

    class Media:
        css = {"all": ("core/partner_admin.css",)}

    @admin.display(description="작업 번호", ordering="pk")
    def order_number(self, obj):
        return f"WO-{obj.created_at:%y%m%d}-{obj.pk:05d}"

    @admin.display(description="견적서")
    def quote_print_link(self, obj):
        url = reverse("partner_admin:partner-workorder-quote", args=[obj.pk])
        return format_html('<a href="{}" target="_blank" rel="noopener">견적서</a>', url)

    @admin.display(description="차량")
    def vehicle_summary(self, obj):
        return " · ".join(value for value in (obj.plate_number, obj.vehicle_model) if value) or "차량 미입력"

    def get_queryset(self, request):
        return super().get_queryset(request).filter(
            partner_id__in=staff_partners(request, booking=True)
        ).select_related("partner", "booking", "created_by")

    def get_form(self, request, obj=None, **kwargs):
        base = super().get_form(request, obj, **kwargs)
        class RequestForm(base):
            def __init__(self, *args, **form_kwargs):
                form_kwargs["request"] = request
                super().__init__(*args, **form_kwargs)
        return RequestForm

    def has_module_permission(self, request):
        return is_system_admin(request) or bool(request.user.is_authenticated and PartnerStaff.objects.filter(
            user=request.user, is_active=True, can_manage_bookings=True, partner__is_active=True
        ).exists())

    def has_view_permission(self, request, obj=None):
        allowed = self.has_module_permission(request)
        return allowed and (obj is None or obj.partner_id in staff_partners(request, booking=True))

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
        partner_ids = list(staff_partners(request, booking=True))
        if obj.partner_id not in partner_ids:
            raise PermissionDenied("담당 협력업체의 작업만 저장할 수 있습니다.")
        previous = None
        if change:
            previous = PartnerWorkOrder.objects.select_for_update().filter(
                pk=obj.pk, partner_id__in=partner_ids
            ).values("status", "quote_status").first()
            if previous is None:
                raise PermissionDenied("해당 작업에 접근할 수 없습니다.")
        # Keep request-specific state on the form; ModelAdmin instances are shared
        # between requests and must not hold mutable per-save state.
        form._previous_status = previous["status"] if previous else None
        booking = form.cleaned_data.get("booking")
        customer = form.cleaned_data.get("customer")
        partner_vehicle = form.cleaned_data.get("partner_vehicle")
        if customer:
            if customer.partner_id != obj.partner_id:
                raise PermissionDenied("고객 대장과 업체가 일치하지 않습니다.")
            obj.customer_name = obj.customer_name or customer.name
            obj.contact_phone = obj.contact_phone or customer.phone
        if partner_vehicle:
            if partner_vehicle.partner_id != obj.partner_id or (customer and partner_vehicle.customer_id != customer.pk):
                raise PermissionDenied("차량 대장과 고객을 확인해 주세요.")
            obj.vehicle_model = obj.vehicle_model or partner_vehicle.model_name
            obj.plate_number = obj.plate_number or partner_vehicle.plate_number
            obj.odometer_km = obj.odometer_km or partner_vehicle.current_odometer_km
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
            obj.assigned_resource = obj.assigned_resource or booking.assigned_resource
        if not change:
            obj.created_by = request.user
        if obj.status == PartnerWorkOrder.Status.COMPLETED and not obj.completed_at:
            obj.completed_at = timezone.now()
        if change and previous["quote_status"] == PartnerWorkOrder.QuoteStatus.SENT:
            # Any edit may change the customer-facing quote (inline items are
            # saved immediately afterwards), so revoke the issued document
            # before persisting the edit and require a fresh share.
            now = timezone.now()
            PartnerQuoteShare.objects.filter(work_order=obj, revoked_at__isnull=True).update(revoked_at=now)
            obj.quote_revision += 1
            obj.quote_status = PartnerWorkOrder.QuoteStatus.DRAFT
            obj.quote_responded_at = None
            obj.quote_decline_reason = ""
            if obj.status == PartnerWorkOrder.Status.WAITING_APPROVAL:
                obj.status = PartnerWorkOrder.Status.QUOTE
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        order = form.instance
        lines = list(order.lines.all())
        line_total = sum(line.amount_krw for line in lines)
        if lines:
            PartnerWorkOrder.objects.filter(pk=order.pk).update(quoted_total_krw=line_total)
            order.quoted_total_krw = line_total
            if order.status == PartnerWorkOrder.Status.COMPLETED and not order.final_total_krw:
                PartnerWorkOrder.objects.filter(pk=order.pk).update(final_total_krw=line_total)
                order.final_total_krw = line_total
        was_completed = getattr(form, "_previous_status", None) == PartnerWorkOrder.Status.COMPLETED
        if order.status != PartnerWorkOrder.Status.COMPLETED or was_completed:
            return

        required = {}
        unlinked_parts = []
        for line in lines:
            if line.kind == PartnerWorkOrderLine.Kind.PART and not line.part_id:
                unlinked_parts.append(line.description)
            if line.kind == PartnerWorkOrderLine.Kind.PART and line.part_id:
                required[line.part_id] = required.get(line.part_id, 0) + int(line.quantity)
        if not required and not unlinked_parts:
            return
        parts = {
            part.pk: part for part in PartnerPart.objects.select_for_update().filter(
                pk__in=required, partner_id=order.partner_id, is_active=True
            ).order_by("pk")
        }
        missing = [part_id for part_id in required if part_id not in parts]
        insufficient = [
            parts[part_id].name for part_id, quantity in required.items()
            if part_id in parts and parts[part_id].stock_quantity < quantity
        ]
        if missing or insufficient or unlinked_parts:
            # The prior value belongs to this request's form, not the shared
            # ModelAdmin instance. Keep a READY/IN_PROGRESS order in its actual
            # previous state when stock validation prevents completion.
            old_status = getattr(form, "_previous_status", None) or PartnerWorkOrder.Status.RECEIVED
            PartnerWorkOrder.objects.filter(pk=order.pk).update(status=old_status, completed_at=None)
            order.status = old_status
            order.completed_at = None
            detail_parts = insufficient + unlinked_parts
            if missing:
                detail_parts.append("비활성화되었거나 다른 업체에 속한 재고 부품")
            detail = ", ".join(detail_parts) if detail_parts else "업체 재고 부품"
            self.message_user(
                request,
                f"재고가 부족해 정비 완료 처리하지 않았습니다: {detail}. 재고를 보충한 뒤 다시 완료해 주세요.",
                level=messages.ERROR,
            )
            return
        for part_id, quantity in required.items():
            part = parts[part_id]
            next_stock = part.stock_quantity - quantity
            PartnerPart.objects.filter(pk=part_id).update(stock_quantity=F("stock_quantity") - quantity)
            PartnerStockMovement.objects.create(
                partner_id=order.partner_id,
                part=part,
                work_order=order,
                direction=PartnerStockMovement.Direction.OUT,
                reason=PartnerStockMovement.Reason.REPAIR_USE,
                quantity=quantity,
                balance_after=next_stock,
                note=f"작업 완료 WO-{order.pk}",
                created_by=request.user,
            )

    def get_inline_instances(self, request, obj=None):
        return [
            PartnerWorkOrderLineInline(self.model, self.admin_site),
            PartnerPaymentInline(self.model, self.admin_site),
        ]


class PartnerWorkOrderLineForm(forms.ModelForm):
    class Meta:
        model = PartnerWorkOrderLine
        fields = ("preset", "kind", "part", "description", "quantity", "unit", "unit_price_krw", "sort_order")

    def __init__(self, *args, request=None, parent=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.request, self.parent = request, parent
        partner_id = getattr(parent, "partner_id", None) or (request.POST.get("partner") if request and request.method == "POST" else None)
        self.fields["part"].queryset = PartnerPart.objects.filter(partner_id=partner_id, is_active=True) if partner_id else PartnerPart.objects.none()
        self.fields["preset"].queryset = PartnerServicePreset.objects.filter(partner_id=partner_id, is_active=True) if partner_id else PartnerServicePreset.objects.none()

    def clean(self):
        data = super().clean()
        part = data.get("part")
        preset = data.get("preset")
        partner_id = getattr(self.parent, "partner_id", None) or (self.request.POST.get("partner") if self.request and self.request.method == "POST" else None)
        if preset and str(preset.partner_id) != str(partner_id):
            self.add_error("preset", "다른 업체의 정비 항목은 선택할 수 없습니다.")
        elif preset:
            data["kind"] = preset.kind
            data["description"] = preset.name
            data["quantity"] = preset.default_quantity
            data["unit"] = preset.unit
            data["unit_price_krw"] = preset.default_price_krw
            if preset.part_id:
                if preset.part.partner_id != int(partner_id):
                    self.add_error("preset", "연결 재고 부품의 업체가 일치하지 않습니다.")
                else:
                    data["part"] = preset.part
        if part and str(part.partner_id) != str(partner_id):
            self.add_error("part", "다른 업체의 재고 부품은 선택할 수 없습니다.")
        if data.get("kind") == PartnerWorkOrderLine.Kind.PART and not part:
            self.add_error("part", "재고 자동 차감을 위해 등록된 부품을 선택해 주세요.")
        quantity = data.get("quantity")
        if data.get("kind") == PartnerWorkOrderLine.Kind.PART and quantity is not None and quantity != quantity.to_integral_value():
            self.add_error("quantity", "재고 부품 수량은 정수로 입력해 주세요.")
        if part and not data.get("description"):
            data["description"] = part.name
        if part and not data.get("unit"):
            data["unit"] = part.unit
        if part and not data.get("unit_price_krw"):
            data["unit_price_krw"] = part.sale_price_krw
        if part and data.get("kind") != PartnerWorkOrderLine.Kind.PART:
            data["kind"] = PartnerWorkOrderLine.Kind.PART
        quantity = data.get("quantity")
        if part and quantity is not None and quantity != quantity.to_integral_value():
            self.add_error("quantity", "재고 차감 수량은 정수로 입력해 주세요.")
        return data


class PartnerWorkOrderLineInline(admin.TabularInline):
    model = PartnerWorkOrderLine
    form = PartnerWorkOrderLineForm
    extra = 1
    fields = ("preset", "kind", "part", "description", "quantity", "unit", "unit_price_krw", "sort_order")
    ordering = ("sort_order", "pk")

    def get_formset(self, request, obj=None, **kwargs):
        base = super().get_formset(request, obj, **kwargs)
        class RequestFormSet(base):
            def __init__(self, *args, **form_kwargs):
                form_kwargs["form_kwargs"] = {"request": request, "parent": obj}
                super().__init__(*args, **form_kwargs)
        return RequestFormSet


class PartnerPaymentInline(admin.TabularInline):
    model = PartnerPayment
    extra = 0
    can_delete = False
    fields = ("paid_at", "provider_name", "provider_transaction_id", "method", "status", "amount_krw", "approval_code")
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False

