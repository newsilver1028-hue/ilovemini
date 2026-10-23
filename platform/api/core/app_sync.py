"""Small change-check endpoint; no member records are exposed publicly."""
import hashlib
import json
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import F, Q
from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.utils import timezone
from rest_framework import generics, permissions, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from . import models

PUBLIC_MODELS = {models.Partner, models.PartnerImage, models.PartnerServiceCategoryOption,
    models.Notice, models.Offer, models.SeasonBanner, models.AppContent, models.AppRelease,
    models.AppRuntimeSettings}
MEMBER_MODELS = {models.Vehicle, models.VehicleOwnership, models.VehiclePlateHistory,
    models.LedgerEntry, models.Reminder, models.PointTransaction, models.AttendanceCheckin,
    models.PointRedemptionRequest, models.PartnerBooking, models.PartnerStaff,
    models.MemberPreference, models.NaverIdentity, models.AppleIdentity,
    models.RecordCorrectionRequest, models.MaintenanceRecommendation, models.ServiceEstimate,
    get_user_model()}

@receiver(post_save, dispatch_uid='app-sync-save')
@receiver(post_delete, dispatch_uid='app-sync-delete')
def changed(sender, instance, using='default', **kwargs):
    if kwargs.get('raw') or sender not in PUBLIC_MODELS | MEMBER_MODELS:
        return
    field = 'public_revision' if sender in PUBLIC_MODELS else 'member_revision'
    transaction.on_commit(lambda: models.AppRuntimeSettings.objects.using(using).filter(pk=1).update(**{field: F(field)+1}), using=using)

@receiver(m2m_changed, sender=get_user_model().groups.through, dispatch_uid='app-sync-groups')
def groups_changed(sender, action, using='default', **kwargs):
    if action in {'post_add', 'post_remove', 'post_clear'}:
        transaction.on_commit(lambda: models.AppRuntimeSettings.objects.using(using).filter(pk=1).update(member_revision=F('member_revision')+1), using=using)

def runtime_configuration():
    setting = models.AppRuntimeSettings.objects.filter(pk=1).first()
    return {'refresh_interval_seconds': min(120, max(10, setting.refresh_interval_seconds if setting else 15)),
        'show_demo_products': setting.show_demo_products if setting else True}

class AppSyncView(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        setting = models.AppRuntimeSettings.objects.filter(pk=1).first()
        now = timezone.now()
        # Include scheduled visibility changes even if no row was saved at that instant.
        windows = {}
        for cls, flag in [(models.AppContent,'is_active'), (models.SeasonBanner,'is_active'),
                (models.Offer,'is_active')]:
            windows[cls.__name__] = list(cls.objects.filter(**{flag:True}, starts_at__lte=now).filter(
                Q(ends_at__isnull=True)|Q(ends_at__gt=now)).values_list('pk',flat=True))
        windows['notices'] = list(models.Notice.objects.filter(is_published=True,published_at__lte=now).filter(
            Q(expires_at__isnull=True)|Q(expires_at__gt=now)).values_list('pk',flat=True))
        windows['revision'] = setting.public_revision if setting else 1
        revision = hashlib.sha256(json.dumps(windows,sort_keys=True).encode()).hexdigest()[:24]
        response = Response({'public_revision': revision,
            'member_revision': str(setting.member_revision if setting else 1) if request.user.is_authenticated else None,
            'configuration': runtime_configuration(),
            'service_categories': list(models.PartnerServiceCategoryOption.objects.filter(is_active=True).values_list('name',flat=True))})
        response['Cache-Control'] = 'private, no-store'
        return response

class PointHistorySerializer(serializers.ModelSerializer):
    transaction_label = serializers.CharField(source='get_transaction_type_display')
    partner_name = serializers.CharField(source='partner.name', default=None)
    class Meta:
        model = models.PointTransaction
        fields = ['id','created_at','transaction_type','transaction_label','points_delta',
            'available_at','partner_name','ledger_entry_id','memo']

class MemberPointHistoryView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PointHistorySerializer
    def get_queryset(self):
        return models.PointTransaction.objects.filter(user=self.request.user).select_related('partner').order_by('-created_at','-pk')
    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request,response,*args,**kwargs)
        response['Cache-Control'] = 'private, no-store'
        return response
