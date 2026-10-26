from django import forms
from django.contrib import admin
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import F

from .models import (
    Partner,
    PartnerFinancialEntry,
    PartnerPart,
    PartnerPurchaseLine,
    PartnerStockMovement,
    PartnerSupplier,
    PartnerWorkOrder,
)
from .partner_admin import active_staff_for, is_system_admin, partner_admin_site, staff_partners


class PartnerScopedAdmin(admin.ModelAdmin):
    """Every workshop record is limited to the signed-in shop membership."""
    list_per_page = 50
    actions = None

    def allowed_partner_ids(self, request):
        return staff_partners(request, booking=True)

    def has_module_permission(self, request):
        return is_system_admin(request) or active_staff_for(request).filter(can_manage_bookings=True).exists()

    def get_queryset(self, request):
        return super().get_queryset(request).filter(partner_id__in=self.allowed_partner_ids(request))

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request) and (
            obj is None or obj.partner_id in self.allowed_partner_ids(request)
        )

    def has_add_permission(self, request):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_view_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return False

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        partner_ids = self.allowed_partner_ids(request)
        if db_field.name == "partner":
            kwargs["queryset"] = Partner.objects.filter(pk__in=partner_ids, is_active=True)
        elif db_field.name == "supplier":
            kwargs["queryset"] = PartnerSupplier.objects.filter(partner_id__in=partner_ids, is_active=True)
        elif db_field.name == "part":
            kwargs["queryset"] = PartnerPart.objects.filter(partner_id__in=partner_ids, is_active=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if obj.partner_id not in self.allowed_partner_ids(request):
            raise PermissionDenied("접근 권한이 없는 업체의 자료입니다.")
        if not change and hasattr(obj, "created_by_id"):
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


class PartnerSupplierAdmin(PartnerScopedAdmin):
    list_display = ("name", "contact_name", "phone", "business_number", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "contact_name", "phone", "business_number")
    fields = ("partner", "name", "contact_name", "phone", "email", "address", "business_number", "note", "is_active")


class PartStockFilter(admin.SimpleListFilter):
    title = "재고 상태"
    parameter_name = "stock"

    def lookups(self, request, model_admin):
        return (("low", "재주문 필요"), ("normal", "기준 재고 초과"))

    def queryset(self, request, queryset):
        if self.value() == "low":
            return queryset.filter(stock_quantity__lte=F("reorder_level"))
        if self.value() == "normal":
            return queryset.filter(stock_quantity__gt=F("reorder_level"))
        return queryset


class PartnerPartAdmin(PartnerScopedAdmin):
    list_display = ("name", "sku", "part_number", "maker", "stock_quantity", "reorder_level", "purchase_price_krw", "sale_price_krw", "stock_state")
    list_filter = ("is_active", "maker", PartStockFilter)
    search_fields = ("name", "sku", "part_number", "maker", "location")
    fields = ("partner", "sku", "part_number", "name", "maker", "unit", "location", "purchase_price_krw", "sale_price_krw", "stock_quantity", "reorder_level", "is_active")
    readonly_fields = ("stock_quantity",)

    @admin.display(description="재고 상태")
    def stock_state(self, obj):
        return "재주문 필요" if obj.stock_quantity <= obj.reorder_level else "정상"


class PartnerPurchaseForm(forms.ModelForm):
    class Meta:
        model = PartnerPurchaseLine
        fields = ("partner", "supplier", "part", "invoice_number", "purchased_at", "quantity", "unit_price_krw", "paid_krw", "note")

    def clean(self):
        data = super().clean()
        if data.get("supplier") and data.get("partner") and data["supplier"].partner_id != data["partner"].pk:
            self.add_error("supplier", "매입처와 업체가 일치하지 않습니다.")
        if data.get("part") and data.get("partner") and data["part"].partner_id != data["partner"].pk:
            self.add_error("part", "부품과 업체가 일치하지 않습니다.")
        quantity, unit_price = data.get("quantity"), data.get("unit_price_krw")
        if quantity and unit_price is not None and quantity * unit_price > 2_000_000_000:
            self.add_error("quantity", "매입 금액이 허용 범위를 초과합니다.")
        total = (quantity or 0) * (unit_price or 0)
        if data.get("paid_krw", 0) > total:
            self.add_error("paid_krw", "지불액이 매입 합계를 초과할 수 없습니다.")
        return data


class PartnerPurchaseAdmin(PartnerScopedAdmin):
    form = PartnerPurchaseForm
    list_display = ("purchased_at", "invoice_number", "supplier", "part", "quantity", "total_krw", "paid_krw", "unpaid_krw")
    list_filter = ("purchased_at", "supplier")
    search_fields = ("invoice_number", "supplier__name", "part__name", "part__sku", "note")
    date_hierarchy = "purchased_at"
    fields = ("partner", "supplier", "part", "invoice_number", "purchased_at", "quantity", "unit_price_krw", "total_krw", "paid_krw", "note", "created_by", "created_at")
    readonly_fields = ("total_krw", "created_by", "created_at")

    @admin.display(description="미지불액")
    def unpaid_krw(self, obj):
        return max(0, obj.total_krw - obj.paid_krw)

    def has_change_permission(self, request, obj=None):
        return obj is None and self.has_module_permission(request)

    @transaction.atomic
    def save_model(self, request, obj, form, change):
        if change:
            raise PermissionDenied("매입 등록은 재고 이력 보존을 위해 수정할 수 없습니다. 조정 기록을 추가해 주세요.")
        partner_id = obj.partner_id
        if partner_id not in self.allowed_partner_ids(request):
            raise PermissionDenied("접근 권한이 없는 업체의 매입입니다.")
        part = PartnerPart.objects.select_for_update().get(pk=obj.part_id, partner_id=partner_id, is_active=True)
        if obj.supplier.partner_id != partner_id:
            raise PermissionDenied("매입처와 업체가 일치하지 않습니다.")
        obj.total_krw = obj.quantity * obj.unit_price_krw
        if obj.paid_krw > obj.total_krw:
            raise ValidationError("지불액이 매입 합계를 초과할 수 없습니다.")
        obj.created_by = request.user
        super().save_model(request, obj, form, change)
        part.stock_quantity = F("stock_quantity") + obj.quantity
        part.purchase_price_krw = obj.unit_price_krw
        part.save(update_fields=("stock_quantity", "purchase_price_krw", "updated_at"))
        part.refresh_from_db(fields=("stock_quantity",))
        PartnerStockMovement.objects.create(
            partner_id=partner_id, part=part, purchase=obj,
            direction=PartnerStockMovement.Direction.IN,
            reason=PartnerStockMovement.Reason.PURCHASE,
            quantity=obj.quantity, balance_after=part.stock_quantity,
            note=f"매입 {obj.invoice_number}".strip(), created_by=request.user,
        )


class PartnerStockMovementForm(forms.ModelForm):
    class Meta:
        model = PartnerStockMovement
        fields = ("partner", "part", "direction", "reason", "quantity", "note")

    def clean(self):
        data = super().clean()
        if data.get("part") and data.get("partner") and data["part"].partner_id != data["partner"].pk:
            self.add_error("part", "부품과 업체가 일치하지 않습니다.")
        return data


class PartnerStockMovementAdmin(PartnerScopedAdmin):
    form = PartnerStockMovementForm
    list_display = ("created_at", "part", "direction", "quantity", "balance_after", "reason", "note", "created_by")
    list_filter = ("direction", "reason", "created_at")
    search_fields = ("part__name", "part__sku", "note")
    date_hierarchy = "created_at"
    fields = ("partner", "part", "direction", "reason", "quantity", "note", "balance_after", "created_by", "created_at")
    readonly_fields = ("balance_after", "created_by", "created_at")

    def has_change_permission(self, request, obj=None):
        return obj is None and self.has_module_permission(request)

    @transaction.atomic
    def save_model(self, request, obj, form, change):
        if change:
            raise PermissionDenied("재고 이동 이력은 수정할 수 없습니다. 반대 조정 기록을 추가해 주세요.")
        if obj.partner_id not in self.allowed_partner_ids(request):
            raise PermissionDenied("접근 권한이 없는 업체의 자료입니다.")
        part = PartnerPart.objects.select_for_update().get(pk=obj.part_id, partner_id=obj.partner_id)
        next_stock = part.stock_quantity + obj.quantity if obj.direction == PartnerStockMovement.Direction.IN else part.stock_quantity - obj.quantity
        if next_stock < 0:
            raise ValidationError("현재고보다 많은 수량을 출고할 수 없습니다.")
        part.stock_quantity = next_stock
        part.save(update_fields=("stock_quantity", "updated_at"))
        obj.balance_after = next_stock
        obj.created_by = request.user
        super().save_model(request, obj, form, change)


class PartnerFinancialEntryAdmin(PartnerScopedAdmin):
    list_display = ("occurred_at", "kind", "category", "counterparty", "amount_krw", "payment_method", "work_order", "note")
    list_filter = ("kind", "category", "payment_method", "occurred_at")
    search_fields = ("category", "counterparty", "note", "work_order__plate_number", "work_order__customer_name")
    date_hierarchy = "occurred_at"
    fields = ("partner", "kind", "category", "occurred_at", "amount_krw", "payment_method", "counterparty", "work_order", "note", "created_by", "created_at")
    readonly_fields = ("created_by", "created_at")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "work_order":
            kwargs["queryset"] = PartnerWorkOrder.objects.filter(partner_id__in=self.allowed_partner_ids(request))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def has_change_permission(self, request, obj=None):
        return obj is None and self.has_module_permission(request)


partner_admin_site.register(PartnerSupplier, PartnerSupplierAdmin)
partner_admin_site.register(PartnerPart, PartnerPartAdmin)
partner_admin_site.register(PartnerPurchaseLine, PartnerPurchaseAdmin)
partner_admin_site.register(PartnerStockMovement, PartnerStockMovementAdmin)
partner_admin_site.register(PartnerFinancialEntry, PartnerFinancialEntryAdmin)
