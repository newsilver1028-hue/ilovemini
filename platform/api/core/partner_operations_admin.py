import hashlib
import secrets
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django import forms
from django.contrib import admin
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import F
from django.http import HttpResponseNotAllowed, HttpResponseRedirect, JsonResponse
from django.urls import path, reverse
from django.utils import timezone
from django.conf import settings
from django.shortcuts import render
import logging

from .models import (
    Partner,
    PartnerFinancialEntry,
    PartnerPart,
    PartnerPurchaseLine,
    PartnerStockMovement,
    PartnerSupplier,
    PartnerWorkOrder,
    PartnerCustomer,
    PartnerVehicle,
    PartnerPosIntegration,
    PartnerPayment,
    PartnerTaxInvoice,
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

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj:
            form.base_fields["partner"].disabled = True
        return form


class PartnerCustomerAdmin(PartnerScopedAdmin):
    list_display = ("name", "phone", "email", "business_number", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name", "phone", "email", "business_number", "address")
    fields = ("partner", "name", "phone", "email", "address", "business_number", "notes", "is_active", "created_at", "updated_at")
    readonly_fields = ("created_at", "updated_at")

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj:
            form.base_fields["partner"].disabled = True
        return form


class PartnerVehicleForm(forms.ModelForm):
    class Meta:
        model = PartnerVehicle
        fields = ("partner", "customer", "plate_number", "manufacturer", "model_name", "model_year", "vin", "first_registration_date", "current_odometer_km", "notes", "is_active")

    def clean(self):
        data = super().clean()
        partner, customer = data.get("partner"), data.get("customer")
        if partner and customer and partner.pk != customer.partner_id:
            self.add_error("customer", "고객과 협력업체가 일치하지 않습니다.")
        return data


class PartnerVehicleAdmin(PartnerScopedAdmin):
    form = PartnerVehicleForm
    list_display = ("plate_number", "manufacturer", "model_name", "customer", "current_odometer_km", "is_active")
    list_filter = ("is_active", "manufacturer", "model_year")
    search_fields = ("plate_number", "model_name", "vin", "customer__name", "customer__phone")
    fields = ("partner", "customer", "plate_number", "manufacturer", "model_name", "model_year", "vin", "first_registration_date", "current_odometer_km", "notes", "is_active")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "customer":
            kwargs["queryset"] = PartnerCustomer.objects.filter(partner_id__in=self.allowed_partner_ids(request), is_active=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj:
            form.base_fields["partner"].disabled = True
        return form


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

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj:
            form.base_fields["partner"].disabled = True
        return form


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
        fields = ("partner", "part", "work_order", "direction", "reason", "quantity", "note")

    def clean(self):
        data = super().clean()
        if data.get("part") and data.get("partner") and data["part"].partner_id != data["partner"].pk:
            self.add_error("part", "부품과 업체가 일치하지 않습니다.")
        if data.get("work_order") and data.get("partner") and data["work_order"].partner_id != data["partner"].pk:
            self.add_error("work_order", "작업과 업체가 일치하지 않습니다.")
        if data.get("reason") == PartnerStockMovement.Reason.REPAIR_USE:
            if data.get("direction") != PartnerStockMovement.Direction.OUT:
                self.add_error("direction", "정비 사용은 재고 출고로 등록해 주세요.")
            if not data.get("work_order"):
                self.add_error("work_order", "정비 사용에는 연결 작업을 지정해야 합니다.")
        return data


class PartnerStockMovementAdmin(PartnerScopedAdmin):
    form = PartnerStockMovementForm
    list_display = ("created_at", "part", "direction", "quantity", "balance_after", "reason", "work_order", "note", "created_by")
    list_filter = ("direction", "reason", "created_at")
    search_fields = ("part__name", "part__sku", "note")
    date_hierarchy = "created_at"
    fields = ("partner", "part", "work_order", "direction", "reason", "quantity", "note", "balance_after", "created_by", "created_at")
    readonly_fields = ("balance_after", "created_by", "created_at")

    def has_change_permission(self, request, obj=None):
        return obj is None and self.has_module_permission(request)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "work_order":
            kwargs["queryset"] = PartnerWorkOrder.objects.filter(partner_id__in=self.allowed_partner_ids(request))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

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

    def get_form(self, request, obj=None, **kwargs):
        base_form = super().get_form(request, obj, **kwargs)

        class PartnerFinanceForm(base_form):
            def clean(self):
                data = super().clean()
                partner = data.get("partner")
                work_order = data.get("work_order")
                if partner and work_order and partner.pk != work_order.partner_id:
                    self.add_error("work_order", "연결 작업과 업체가 일치하지 않습니다.")
                return data

        return PartnerFinanceForm

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "work_order":
            kwargs["queryset"] = PartnerWorkOrder.objects.filter(partner_id__in=self.allowed_partner_ids(request))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def has_change_permission(self, request, obj=None):
        return obj is None and self.has_module_permission(request)


partner_admin_site.register(PartnerSupplier, PartnerSupplierAdmin)
partner_admin_site.register(PartnerPart, PartnerPartAdmin)
partner_admin_site.register(PartnerCustomer, PartnerCustomerAdmin)
partner_admin_site.register(PartnerVehicle, PartnerVehicleAdmin)
partner_admin_site.register(PartnerPurchaseLine, PartnerPurchaseAdmin)
partner_admin_site.register(PartnerStockMovement, PartnerStockMovementAdmin)
partner_admin_site.register(PartnerFinancialEntry, PartnerFinancialEntryAdmin)


class PartnerPosIntegrationAdmin(PartnerScopedAdmin):
    change_form_template = "admin/core/partnerposintegration/change_form.html"
    list_display = ("partner", "provider_name", "is_active", "last_received_at")
    fields = ("partner", "provider_name", "is_active", "webhook_url", "event_contract", "last_received_at", "created_at", "updated_at")
    readonly_fields = ("webhook_url", "event_contract", "last_received_at", "created_at", "updated_at")

    @admin.display(description="수신 주소")
    def webhook_url(self, obj):
        if not obj or not obj.pk:
            return "저장 후 생성됩니다."
        return "/api/partner-pos/events/"

    @admin.display(description="수신 규격")
    def event_contract(self, obj):
        return 'POST JSON · Authorization: Bearer {토큰} · {"event_id":"거래고유값","work_order_id":123,"status":"approved|cancelled","method":"card|cash|transfer|easy_pay|other","amount_krw":55000,"approval_code":"승인번호","paid_at":"ISO-8601"} · 취소는 승인 거래의 event_id와 work_order_id를 그대로 사용합니다.'

    def get_urls(self):
        return [path("<path:object_id>/rotate-token/", self.admin_site.admin_view(self.rotate_token), name="partner-pos-rotate-token")] + super().get_urls()

    def rotate_token(self, request, object_id):
        change_url = reverse("partner_admin:core_partnerposintegration_change", args=[object_id])
        if request.method != "POST":
            return HttpResponseRedirect(change_url)
        integration = self.get_object(request, object_id)
        if integration is None or integration.partner_id not in self.allowed_partner_ids(request):
            raise PermissionDenied("접근 권한이 없습니다.")
        token = secrets.token_urlsafe(36)
        integration.token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        integration.is_active = True
        integration.save(update_fields=("token_hash", "is_active", "updated_at"))
        self.message_user(
            request,
            f"POS 수신 토큰(이 화면에서만 표시): {token} · 주소: /api/partner-pos/events/ · POS 프로그램에 Bearer 토큰으로 설정하세요.",
            level="success",
        )
        return HttpResponseRedirect(change_url)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj:
            form.base_fields["partner"].disabled = True
        return form

    def save_model(self, request, obj, form, change):
        if change:
            obj.partner_id = self.get_object(request, obj.pk).partner_id
        super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        return False


class PartnerPaymentAdmin(PartnerScopedAdmin):
    list_display = ("paid_at", "work_order", "provider_name", "method", "status", "amount_krw", "provider_transaction_id", "approval_code")
    list_filter = ("provider_name", "method", "status", "paid_at")
    search_fields = ("provider_transaction_id", "approval_code", "work_order__plate_number", "work_order__customer_name")
    readonly_fields = tuple(field.name for field in PartnerPayment._meta.fields)
    fields = ("partner", "work_order", "provider_name", "provider_transaction_id", "method", "status", "amount_krw", "approval_code", "paid_at", "created_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return self.has_view_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return False


class PartnerTaxInvoiceForm(forms.ModelForm):
    items = forms.JSONField(
        label="품목",
        required=False,
        help_text="작업지시에서 불러오거나 아래 표에 품목·수량·단가를 입력하세요. 금액은 수량×단가로 계산됩니다.",
        widget=forms.Textarea(attrs={"rows": 5, "class": "invoice-items-source", "spellcheck": "false"}),
    )

    class Meta:
        model = PartnerTaxInvoice
        fields = "__all__"

    def clean_items(self):
        raw_items = self.cleaned_data.get("items") or []
        if not isinstance(raw_items, list):
            raise ValidationError("품목은 목록 형식이어야 합니다.")
        if len(raw_items) > 99:
            raise ValidationError("품목은 최대 99개까지 입력할 수 있습니다.")

        items = []
        for index, raw in enumerate(raw_items, start=1):
            if not isinstance(raw, dict):
                raise ValidationError(f"{index}번 품목 형식을 확인해 주세요.")
            description = str(raw.get("description", "")).strip()
            if not description:
                continue
            if len(description) > 100:
                raise ValidationError(f"{index}번 품목명은 100자 이내로 입력해 주세요.")
            try:
                quantity = Decimal(str(raw.get("quantity", "1")))
                price_value = Decimal(str(raw.get("unit_price_krw", 0)))
            except (InvalidOperation, TypeError, ValueError):
                raise ValidationError(f"{index}번 품목의 수량과 단가를 확인해 주세요.")
            if not quantity.is_finite() or quantity <= 0 or quantity > Decimal("1000000"):
                raise ValidationError(f"{index}번 품목의 수량은 0보다 큰 값이어야 합니다.")
            if not price_value.is_finite() or price_value < 0 or price_value != price_value.to_integral_value():
                raise ValidationError(f"{index}번 품목의 단가는 0 이상의 원 단위로 입력해 주세요.")
            unit_price = int(price_value)
            amount = int((quantity * unit_price).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
            items.append({
                "description": description,
                "quantity": format(quantity.normalize(), "f"),
                "unit_price_krw": unit_price,
                "amount_krw": amount,
            })
        return items

    def clean(self):
        data = super().clean()
        partner, work_order = data.get("partner"), data.get("work_order")
        if partner and work_order and partner.pk != work_order.partner_id:
            self.add_error("work_order", "정비 작업과 협력업체가 일치하지 않습니다.")

        supply = data.get("supply_cost_krw")
        tax = data.get("tax_krw")
        total = data.get("total_krw")
        if supply is not None and tax is not None and total is not None and total != supply + tax:
            self.add_error("total_krw", "합계는 공급가액과 세액의 합이어야 합니다.")
        if supply is not None and tax is not None:
            tax_type = data.get("tax_type")
            if tax_type in (PartnerTaxInvoice.TaxType.EXEMPT, PartnerTaxInvoice.TaxType.ZERO) and tax != 0:
                self.add_error("tax_krw", "면세·영세 계산서의 세액은 0원이어야 합니다.")
            elif tax_type == PartnerTaxInvoice.TaxType.TAXABLE and total is not None:
                expected_supply = int((Decimal(total) / Decimal("1.1")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
                expected_tax = total - expected_supply
                if supply != expected_supply or tax != expected_tax:
                    self.add_error("tax_krw", f"과세 금액 기준 세액은 {expected_tax:,}원이어야 합니다.")

        for field in ("seller_business_number", "buyer_business_number"):
            value = "".join(char for char in data.get(field, "") if char.isdigit())
            if value and len(value) != 10:
                self.add_error(field, "사업자등록번호 10자리를 확인해 주세요.")
            data[field] = value
        if data.get("status") == PartnerTaxInvoice.Status.ISSUED and not data.get("provider_document_id"):
            self.add_error("provider_document_id", "실제 발행을 확인할 대행사 문서번호가 필요합니다.")
        if data.get("status") == PartnerTaxInvoice.Status.ISSUED:
            for field in ("seller_business_number", "seller_name", "seller_representative", "buyer_business_number", "buyer_name", "buyer_representative"):
                if not data.get(field):
                    self.add_error(field, "외부 발행 확인에는 공급자와 공급받는자 정보가 필요합니다.")
        return data


class PartnerTaxInvoiceAdmin(PartnerScopedAdmin):
    form = PartnerTaxInvoiceForm
    change_form_template = "admin/core/partnertaxinvoice/change_form.html"
    list_display = ("write_date", "buyer_name", "work_order", "tax_type", "total_krw", "status", "provider_name", "provider_document_id")
    list_filter = ("status", "tax_type", "purpose", "write_date")
    search_fields = ("buyer_name", "buyer_business_number", "seller_name", "provider_document_id", "work_order__plate_number")
    date_hierarchy = "write_date"
    fields = (
        "partner", "work_order", "status", "tax_type", "purpose", "write_date",
        ("seller_business_number", "seller_name"), ("seller_representative", "seller_email"), "seller_address",
        ("buyer_business_number", "buyer_name"), ("buyer_representative", "buyer_email"), "buyer_address",
        ("supply_cost_krw", "tax_krw", "total_krw"), "items",
        ("provider_name", "provider_user_id", "provider_document_id"), "provider_error_code", "issued_at", "created_by_display", "created_at",
    )
    readonly_fields = ("status", "provider_error_code", "issued_at", "created_by_display", "created_at")

    @admin.display(description="등록자")
    def created_by_display(self, obj):
        if not obj or not obj.pk:
            return "저장 시 로그인 계정 자동 기록"
        return obj.created_by or "기록 없음"

    def has_change_permission(self, request, obj=None):
        return self.has_view_permission(request, obj) and (obj is None or obj.status == PartnerTaxInvoice.Status.DRAFT)

    def get_urls(self):
        custom_urls = [
            path("tax-invoice-work-orders/", self.admin_site.admin_view(self.work_order_options), name="partner-taxinvoice-work-orders"),
            path("<path:object_id>/issue/", self.admin_site.admin_view(self.issue_invoice), name="partner-taxinvoice-issue"),
        ]
        return custom_urls + super().get_urls()

    def work_order_options(self, request):
        if request.method != "GET":
            return HttpResponseNotAllowed(["GET"])
        try:
            partner_id = int(request.GET.get("partner_id", ""))
        except (TypeError, ValueError):
            return JsonResponse({"error": "업체를 먼저 선택해 주세요."}, status=400)
        if not Partner.objects.filter(pk=partner_id, pk__in=self.allowed_partner_ids(request)).exists():
            return JsonResponse({"error": "접근 권한이 없는 업체입니다."}, status=403)

        orders = PartnerWorkOrder.objects.filter(partner_id=partner_id).select_related(
            "customer"
        ).prefetch_related("lines").order_by("-pk")
        results = []
        for order in orders:
            vehicle = order.plate_number or order.vehicle_model or "차량 미등록"
            lines = [{
                "description": line.description,
                "quantity": str(line.quantity),
                "unit_price_krw": line.unit_price_krw,
                "amount_krw": line.amount_krw,
            } for line in order.lines.all()]
            total = order.final_total_krw or order.quoted_total_krw
            results.append({
                "id": order.pk,
                "label": f"WO-{order.pk} · {vehicle} · {order.get_status_display()}",
                "buyer_name": order.customer.name if order.customer_id else order.customer_name,
                "buyer_business_number": order.customer.business_number if order.customer_id else "",
                "buyer_representative": "",
                "buyer_email": order.customer.email if order.customer_id else "",
                "buyer_address": order.customer.address if order.customer_id else "",
                "total_krw": total,
                "items": lines,
            })
        return JsonResponse({"work_orders": results})

    def issue_invoice(self, request, object_id):
        invoice = self.get_object(request, object_id)
        if invoice is None or not self.has_change_permission(request, invoice):
            raise PermissionDenied("접근 권한이 없습니다.")
        if invoice.status != PartnerTaxInvoice.Status.DRAFT:
            self.message_user(request, "발행 준비 상태 문서만 외부 발행할 수 있습니다.", level="error")
            return HttpResponseRedirect(reverse("partner_admin:core_partnertaxinvoice_change", args=[invoice.pk]))
        confirmation_context = {
            **self.admin_site.each_context(request),
            "title": "전자세금계산서 발행 확인",
            "opts": self.model._meta,
            "invoice": invoice,
            "change_url": reverse("partner_admin:core_partnertaxinvoice_change", args=[invoice.pk]),
            "is_test": getattr(settings, "POPBILL_IS_TEST", True),
        }
        if request.method != "POST":
            return render(request, "admin/core/partnertaxinvoice/issue_confirm.html", confirmation_context)
        item_rows = invoice.items if isinstance(invoice.items, list) else []
        if not any(isinstance(item, dict) and str(item.get("description", "")).strip() for item in item_rows):
            self.message_user(request, "실제 발행 전에 품목을 한 줄 이상 입력해 주세요.", level="error")
            return HttpResponseRedirect(confirmation_context["change_url"])
        if not getattr(settings, "POPBILL_LINK_ID", "") or not getattr(settings, "POPBILL_SECRET_KEY", ""):
            self.message_user(request, "Render 환경변수 POPBILL_LINK_ID와 POPBILL_SECRET_KEY를 먼저 설정해 주세요.", level="error")
            return HttpResponseRedirect(confirmation_context["change_url"])
        if not invoice.provider_user_id:
            self.message_user(request, "해당 업체의 팝빌 사용자 ID를 입력한 뒤 발행해 주세요.", level="error")
            return HttpResponseRedirect(confirmation_context["change_url"])
        if not all((invoice.seller_business_number, invoice.seller_name, invoice.seller_representative,
                    invoice.buyer_business_number, invoice.buyer_name, invoice.buyer_representative)):
            self.message_user(request, "공급자·공급받는자 사업자 정보가 모두 필요합니다.", level="error")
            return HttpResponseRedirect(confirmation_context["change_url"])
        try:
            from popbill import PopbillException, Taxinvoice, TaxinvoiceDetail, TaxinvoiceService
            service = TaxinvoiceService(settings.POPBILL_LINK_ID, settings.POPBILL_SECRET_KEY)
            service.IsTest = getattr(settings, "POPBILL_IS_TEST", True)
            service.IPRestrictOnOff = getattr(settings, "POPBILL_IP_RESTRICT", False)
            service.UseStaticIP = False
            service.UseLocalTimeYN = True
            mgt_key = f"ILM-TI-{invoice.pk}"
            tax_type = {
                PartnerTaxInvoice.TaxType.TAXABLE: "과세",
                PartnerTaxInvoice.TaxType.EXEMPT: "면세",
                PartnerTaxInvoice.TaxType.ZERO: "영세",
            }[invoice.tax_type]
            document = Taxinvoice(
                writeDate=invoice.write_date.strftime("%Y%m%d"),
                chargeDirection="정과금", issueType="정발행",
                purposeType="청구" if invoice.purpose == PartnerTaxInvoice.Purpose.BILL else "영수",
                taxType=tax_type,
                invoicerCorpNum="".join(ch for ch in invoice.seller_business_number if ch.isdigit()),
                invoicerCorpName=invoice.seller_name, invoicerMgtKey=mgt_key,
                invoicerCEOName=invoice.seller_representative,
                invoicerAddr=invoice.seller_address or "", invoicerBizClass="", invoicerBizType="",
                invoicerContactName=invoice.seller_representative, invoicerEmail=invoice.seller_email or "",
                invoiceeType="사업자",
                invoiceeCorpNum="".join(ch for ch in invoice.buyer_business_number if ch.isdigit()),
                invoiceeCorpName=invoice.buyer_name, invoiceeCEOName=invoice.buyer_representative,
                invoiceeAddr=invoice.buyer_address or "", invoiceeBizClass="", invoiceeBizType="",
                invoiceeContactName1=invoice.buyer_representative, invoiceeEmail1=invoice.buyer_email or "",
                supplyCostTotal=str(invoice.supply_cost_krw), taxTotal=str(invoice.tax_krw),
                totalAmount=str(invoice.total_krw), invoicerSMSSendYN=False,
            )
            item_rows = invoice.items if isinstance(invoice.items, list) else []
            normalized = [item for item in item_rows if isinstance(item, dict) and item.get("description")]
            if not normalized:
                normalized = [{"description": f"정비 작업 WO-{invoice.work_order_id}", "quantity": 1, "amount_krw": invoice.total_krw}]
            normalized = normalized[:99]
            detail_list = []
            remaining_supply, remaining_tax = invoice.supply_cost_krw, invoice.tax_krw
            gross_values = [max(0, int(item.get("amount_krw", 0))) for item in normalized]
            gross_total = sum(gross_values) or invoice.total_krw
            for index, (item, gross) in enumerate(zip(normalized, gross_values)):
                is_last = index == len(normalized) - 1
                supply = remaining_supply if is_last else round(invoice.supply_cost_krw * gross / gross_total)
                tax = remaining_tax if is_last else round(invoice.tax_krw * gross / gross_total)
                remaining_supply -= supply
                remaining_tax -= tax
                detail_list.append(TaxinvoiceDetail(
                    serialNum=index + 1,
                    purchaseDT=invoice.write_date.strftime("%Y%m%d"),
                    itemName=str(item["description"])[:100], spec="",
                    qty=str(item.get("quantity", 1)),
                    unitCost=str(item.get("unit_price_krw", supply)),
                    supplyCost=str(supply), tax=str(tax), remark="",
                ))
            document.detailList = detail_list
            response = service.registIssue(
                "".join(ch for ch in invoice.seller_business_number if ch.isdigit()),
                document, False, False, "", "", "", invoice.provider_user_id
            )
            if getattr(response, "code", None) != 1:
                code = str(getattr(response, "code", "발행오류"))[:40]
                invoice.provider_error_code = code
                invoice.save(update_fields=("provider_error_code",))
                self.message_user(request, f"팝빌 발행 실패 ({code}). 문서 상태를 발행으로 변경하지 않았습니다.", level="error")
                return HttpResponseRedirect(confirmation_context["change_url"])
            invoice.status = PartnerTaxInvoice.Status.ISSUED
            invoice.provider_name = "팝빌"
            invoice.provider_document_id = getattr(response, "ntsConfirmNum", "") or mgt_key
            invoice.issued_at = timezone.now()
            invoice.provider_error_code = ""
            invoice.save(update_fields=("status", "provider_name", "provider_document_id", "issued_at", "provider_error_code"))
            self.message_user(request, f"팝빌 발행 요청을 처리했습니다. 문서번호: {invoice.provider_document_id}", level="success")
        except ImportError:
            self.message_user(request, "팝빌 SDK를 사용할 수 없습니다. 서버 배포 상태를 확인해 주세요.", level="error")
        except Exception as exc:
            code = str(getattr(exc, "code", "발행오류"))[:40]
            invoice.provider_error_code = code
            invoice.save(update_fields=("provider_error_code",))
            logging.getLogger(__name__).exception("Tax invoice issue failed (invoice_id=%s, code=%s)", invoice.pk, code)
            self.message_user(request, f"팝빌 발행 실패 ({code}). 업체 계정·인증서·충전 포인트와 입력 정보를 확인해 주세요.", level="error")
        return HttpResponseRedirect(confirmation_context["change_url"])

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        order_id = request.GET.get("work_order")
        if order_id:
            order = PartnerWorkOrder.objects.select_related("partner", "customer").filter(
                pk=order_id, partner_id__in=self.allowed_partner_ids(request)
            ).first()
            if order:
                lines = list(order.lines.all())
                total = order.final_total_krw or order.quoted_total_krw
                initial.update({
                    "partner": order.partner_id,
                    "work_order": order.pk,
                    "buyer_name": (order.customer.name if order.customer_id else order.customer_name),
                    "buyer_business_number": order.customer.business_number if order.customer_id else "",
                    "buyer_email": order.customer.email if order.customer_id else "",
                    "buyer_address": order.customer.address if order.customer_id else "",
                    "supply_cost_krw": round(total / 1.1) if total else 0,
                    "tax_krw": total - round(total / 1.1) if total else 0,
                    "total_krw": total,
                    "items": [{"description": line.description, "quantity": str(line.quantity), "unit_price_krw": line.unit_price_krw, "amount_krw": line.amount_krw} for line in lines],
                })
        return initial

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "work_order":
            kwargs["queryset"] = PartnerWorkOrder.objects.filter(partner_id__in=self.allowed_partner_ids(request)).select_related("partner")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if obj.work_order.partner_id != obj.partner_id:
            raise PermissionDenied("정비 작업과 협력업체가 일치하지 않습니다.")
        if obj.status == PartnerTaxInvoice.Status.ISSUED and not obj.issued_at:
            obj.issued_at = timezone.now()
        if not change:
            obj.created_by = request.user
            if not obj.items:
                obj.items = [{"description": line.description, "quantity": str(line.quantity), "unit_price_krw": line.unit_price_krw, "amount_krw": line.amount_krw} for line in obj.work_order.lines.all()]
        super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        return False


partner_admin_site.register(PartnerPosIntegration, PartnerPosIntegrationAdmin)
partner_admin_site.register(PartnerPayment, PartnerPaymentAdmin)
partner_admin_site.register(PartnerTaxInvoice, PartnerTaxInvoiceAdmin)
