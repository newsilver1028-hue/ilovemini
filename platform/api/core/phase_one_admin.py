from django import forms
from django.contrib import admin, messages
from django.contrib.admin.widgets import AdminDateWidget
from django.db import transaction
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.shortcuts import get_object_or_404, redirect
from django.utils.html import format_html
from .models import ServiceEstimate, MaintenanceRecommendation, PartnerBooking, LedgerEntry, VehicleOwnership, PartnerStaff
from .models import PartnerWorkOrder, PartnerWorkOrderLine
from .phase_one_views import EstimateSerializer, RecommendationSerializer

class EstimateItemsWidget(forms.Textarea):
    template_name = 'admin/estimate_items_widget.html'

class PhaseOneForm(forms.ModelForm):
    def clean(self):
        data = super().clean()
        if self.errors or self.instance.pk:
            return data
        serializer_type = EstimateSerializer if self._meta.model is ServiceEstimate else RecommendationSerializer
        payload = dict(data)
        key = 'booking' if self._meta.model is ServiceEstimate else 'entry'
        payload[key] = payload[key].pk
        for name in ['due_date']:
            if payload.get(name): payload[name] = payload[name].isoformat()
        serializer = serializer_type(data=payload, context={'request': self.request})
        if not serializer.is_valid():
            raise forms.ValidationError(str(serializer.errors))
        return data

class EstimateForm(PhaseOneForm):
    class Meta:
        model = ServiceEstimate
        fields = ['booking','items','note']
        labels = {'booking': '연결 예약'}
        widgets = {'items': EstimateItemsWidget}

class RecommendationForm(PhaseOneForm):
    class Meta:
        model = MaintenanceRecommendation
        fields = ['entry','title','due_date','due_odometer_km']
        widgets = {'due_date': AdminDateWidget}

class PhaseOneAdmin(admin.ModelAdmin):
    change_list_template = "admin/core/change_list_with_calendar.html"
    def allowed_partners(self, request):
        if not request.user.is_authenticated: return PartnerStaff.objects.none().values_list("partner_id", flat=True)
        field = 'can_manage_bookings' if self.model is ServiceEstimate else 'can_verify_records'
        return PartnerStaff.objects.filter(user=request.user,is_active=True,partner__is_active=True,**{field:True}).values_list('partner_id',flat=True)
    def has_module_permission(self, request):
        return request.user.is_superuser or self.allowed_partners(request).exists()
    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request) and (obj is None or request.user.is_superuser or (obj.booking.partner_id if self.model is ServiceEstimate else obj.entry.partner_id) in self.allowed_partners(request))
    def has_add_permission(self, request): return self.has_module_permission(request)
    def has_change_permission(self, request, obj=None): return self.has_view_permission(request,obj)
    def has_delete_permission(self, request, obj=None): return False
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser: return qs
        key = 'booking__partner_id__in' if self.model is ServiceEstimate else 'entry__partner_id__in'
        return qs.filter(**{key:self.allowed_partners(request)})
    def get_readonly_fields(self, request, obj=None):
        return tuple(field.name for field in self.model._meta.fields) if obj else ()
    def get_form(self, request, obj=None, **kwargs):
        base = super().get_form(request,obj,**kwargs)
        class RequestForm(base): pass
        RequestForm.request=request
        return RequestForm
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'booking':
            qs=PartnerBooking.objects.filter(status__in=['requested','confirmed'])
            if not request.user.is_superuser: qs=qs.filter(partner_id__in=self.allowed_partners(request))
            kwargs['queryset']=qs
        elif db_field.name == 'entry':
            qs=LedgerEntry.objects.filter(source='partner')
            if not request.user.is_superuser: qs=qs.filter(partner_id__in=self.allowed_partners(request))
            kwargs['queryset']=qs
        return super().formfield_for_foreignkey(db_field,request,**kwargs)
    def save_model(self, request, obj, form, change):
        if change: raise PermissionDenied('전송한 원본은 변경할 수 없습니다. 새 견적 또는 새 권장을 작성해 주세요.')
        with transaction.atomic():
            if self.model is ServiceEstimate:
                booking=PartnerBooking.objects.select_for_update().get(pk=obj.booking_id)
                if booking.status not in ['requested','confirmed']: raise PermissionDenied('진행할 수 없는 예약입니다.')
                last=ServiceEstimate.objects.filter(booking=booking).order_by('-revision').first()
                obj.revision=last.revision+1 if last else 1
                obj.total_krw=sum(item['amount_krw'] for item in obj.items)
                obj.status='sent'
                ServiceEstimate.objects.filter(booking=booking,status='sent').update(status='superseded')
            else:
                ownership=VehicleOwnership.objects.get(vehicle=obj.entry.vehicle,ended_at__isnull=True)
                obj.member=ownership.user
            super().save_model(request,obj,form,change)

class EstimateAdmin(PhaseOneAdmin):
    form=EstimateForm
    change_list_template = "admin/core/serviceestimate/change_list.html"
    list_display=['id','booking','revision','total_krw','status','created_at','print_document','work_order_button']

    actions = None

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("booking__partner", "booking__work_order")

    def changelist_view(self, request, extra_context=None):
        estimate_id = request.POST.get("convert_estimate")
        if request.method == "POST" and estimate_id is not None:
            if not self.has_change_permission(request) or not estimate_id.isascii() or not estimate_id.isdecimal() or len(estimate_id) > 18:
                raise PermissionDenied
            estimate = get_object_or_404(self.get_queryset(request), pk=estimate_id)
            if not self.has_change_permission(request, estimate) or not estimate.booking.partner.is_active:
                raise PermissionDenied
            response = self.create_work_order(request, self.get_queryset(request).filter(pk=estimate.pk))
            return response or redirect(reverse(f"{self.admin_site.name}:core_serviceestimate_changelist"))
        return super().changelist_view(request, extra_context)

    @admin.display(description="작업지시")
    def work_order_button(self, obj):
        booking = obj.booking
        if not booking.partner.is_active:
            return "—"
        order = getattr(booking, "work_order", None)
        if order and order.partner_id == booking.partner_id:
            url = reverse(f"{self.admin_site.name}:core_partnerworkorder_change", args=[order.pk])
            return format_html('<a class="button" href="{}">작업지시 열기</a>', url)
        if booking.status in (PartnerBooking.Status.REQUESTED, PartnerBooking.Status.CONFIRMED) and obj.status not in ("declined", "superseded"):
            return format_html('<button type="submit" class="button" name="convert_estimate" value="{}">작업지시로 전환</button>', obj.pk)
        return "—"

    def create_work_order(self, request, queryset):
        estimate_ids = list(queryset.values_list("pk", flat=True)[:2])
        if len(estimate_ids) != 1:
            self.message_user(request, "전환할 견적을 한 건만 선택해 주세요.", messages.WARNING)
            return
        with transaction.atomic():
            estimate = self.get_queryset(request).get(pk=estimate_ids[0])
            booking = PartnerBooking.objects.select_for_update().get(pk=estimate.booking_id)
            if not booking.partner.is_active:
                raise PermissionDenied
            estimate.refresh_from_db()
            order = PartnerWorkOrder.objects.filter(booking=booking, partner=booking.partner).first()
            if order is None:
                if booking.status not in (PartnerBooking.Status.REQUESTED, PartnerBooking.Status.CONFIRMED) or estimate.status in ("declined", "superseded"):
                    self.message_user(request, "진행 가능한 예약의 유효한 견적만 전환할 수 있습니다.", messages.WARNING)
                    return
                vehicle = booking.vehicle
                order = PartnerWorkOrder.objects.create(
                    partner=booking.partner, booking=booking, vehicle=vehicle,
                    contact_phone=booking.contact_phone,
                    vehicle_model=vehicle.model_name if vehicle else "",
                    plate_number=vehicle.plate_number if vehicle else "",
                    odometer_km=vehicle.current_odometer_km if vehicle else None,
                    customer_concern=booking.customer_note,
                    assigned_resource=booking.assigned_resource,
                    items=estimate.items, quoted_total_krw=estimate.total_krw,
                    created_by=request.user,
                )
                PartnerWorkOrderLine.objects.bulk_create([
                    PartnerWorkOrderLine(
                        work_order=order, kind=PartnerWorkOrderLine.Kind.OTHER,
                        description=item["title"], quantity=1,
                        unit_price_krw=item["amount_krw"], sort_order=index,
                    )
                    for index, item in enumerate(estimate.items)
                ])
                self.message_user(request, "차량 정보와 견적 항목을 작업지시로 옮겼습니다.", messages.SUCCESS)
            else:
                self.message_user(request, "이 예약에 연결된 기존 작업지시를 열었습니다.", messages.INFO)
        return redirect(reverse(f"{self.admin_site.name}:core_partnerworkorder_change", args=[order.pk]))

    @admin.display(description='견적서 출력')
    def print_document(self, obj):
        url = reverse('partner_admin:partner-estimate-print', args=[obj.pk])
        return format_html('<a href="{}" target="_blank" rel="noopener">인쇄 · PDF</a>', url)
class RecommendationAdmin(PhaseOneAdmin):
    form=RecommendationForm
    list_display=['id','entry','title','due_date','due_odometer_km','status']
