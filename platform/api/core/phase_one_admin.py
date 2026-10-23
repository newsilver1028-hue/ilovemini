from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import AdminDateWidget
from django.db import transaction
from django.core.exceptions import PermissionDenied
from .models import ServiceEstimate, MaintenanceRecommendation, PartnerBooking, LedgerEntry, VehicleOwnership, PartnerStaff
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
    list_display=['id','booking','revision','total_krw','status','created_at']
class RecommendationAdmin(PhaseOneAdmin):
    form=RecommendationForm
    list_display=['id','entry','title','due_date','due_odometer_km','status']
