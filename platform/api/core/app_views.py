"""Account-scoped app preferences and immutable correction requests."""
from django.db import transaction
from django.db.models import Q, F
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .member_display import member_nickname
from .member_roles import GRADES, member_grade
from .models import AppContent, AppRelease, MemberPreference, RecordCorrectionRequest, Vehicle, PartnerStaff, LedgerEntry, PartnerBooking

def active_vehicles(user):
    return Vehicle.objects.filter(status='active', ownerships__user=user, ownerships__ended_at__isnull=True).distinct()
def verification_partners(user):
    return PartnerStaff.objects.filter(user=user, is_active=True, can_verify_records=True, partner__is_active=True).values_list('partner_id', flat=True)

class AppContentView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    def get(self, request):
        now = timezone.now()
        items = AppContent.objects.filter(is_active=True, starts_at__lte=now).filter(Q(ends_at__isnull=True) | Q(ends_at__gt=now))
        def public(item):
            return {'id': item.pk, 'title': item.title, 'category': item.category, 'description': item.description,
                'image_url': item.image_url if item.image_url.startswith('https://') else '', 'asset_key': item.asset_key,
                'action_url': item.action_url if item.action_url.startswith('https://') else '',
                'price_krw': item.price_krw, 'compatible_models': item.compatible_models}
        products = [public(item) for item in items if item.kind == 'product' and item.action_url.startswith('https://')]
        banners = [public(item) for item in items if item.kind == 'banner']
        releases = [{'platform': item.platform, 'version': item.version, 'build_number': item.build_number,
            'download_url': item.download_url, 'notes': item.notes} for item in AppRelease.objects.filter(is_active=True) if item.download_url.startswith('https://')]
        response = Response({'banners': banners, 'products': products, 'releases': releases})
        response['Cache-Control'] = 'no-store'
        return response

class MemberPreferenceView(APIView):
    permission_classes = [IsAuthenticated]
    @transaction.atomic
    def get(self, request):
        preference, _ = MemberPreference.objects.get_or_create(user=request.user)
        preference = MemberPreference.objects.select_for_update().get(pk=preference.pk)
        vehicles = active_vehicles(request.user)
        if not vehicles.filter(pk=preference.primary_vehicle_id).exists():
            preference.primary_vehicle = vehicles.first()
            preference.save(update_fields=['primary_vehicle'])
        return Response({'primary_vehicle_id': preference.primary_vehicle_id})
    @transaction.atomic
    def patch(self, request):
        vehicle_id = serializers.IntegerField(min_value=1).run_validation(request.data.get('primary_vehicle_id'))
        vehicle = active_vehicles(request.user).filter(pk=vehicle_id).first()
        if vehicle is None: raise NotFound('현재 이용 중인 차량만 대표 차량으로 선택할 수 있습니다.')
        preference, _ = MemberPreference.objects.get_or_create(user=request.user)
        preference = MemberPreference.objects.select_for_update().get(pk=preference.pk)
        preference.primary_vehicle = vehicle; preference.save(update_fields=['primary_vehicle'])
        return Response({'primary_vehicle_id': vehicle.pk})

class MemberOverviewView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user; grade = member_grade(user); vehicles = active_vehicles(user)
        bookings = PartnerBooking.objects.filter(customer=user)
        verified = LedgerEntry.objects.filter(source='partner', vehicle__in=vehicles, vehicle__ownerships__user=user,
            vehicle__ownerships__ended_at__isnull=True, created_at__gte=F('vehicle__ownerships__started_at')).distinct().count()
        return Response({'member_id': user.pk, 'nickname': member_nickname(user), 'email': user.email, 'grade': grade,
            'grade_label': GRADES[grade], 'vehicle_count': vehicles.count(), 'booking_count': bookings.count(),
            'active_booking_count': bookings.filter(status__in=['requested','confirmed']).count(), 'verified_record_count': verified})

class PassportPreviewView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        if not verification_partners(request.user).exists(): raise PermissionDenied('QR 차량 조회 권한이 있는 협력업체 담당자만 이용할 수 있습니다.')
        value = serializers.UUIDField().run_validation(request.data.get('vehicle_public_id'))
        vehicle = Vehicle.objects.filter(public_id=value, status='active', ownerships__ended_at__isnull=True, ownerships__user__isnull=False).first()
        if vehicle is None: raise NotFound('이용 중인 차량 QR이 아닙니다.')
        return Response({'public_id': str(vehicle.public_id), 'model_name': vehicle.model_name, 'manufacturer': vehicle.manufacturer,
            'plate_number': vehicle.plate_number, 'current_odometer_km': vehicle.current_odometer_km})

def correction_payload(item):
    entry = item.entry
    return {'id': item.pk, 'reason': item.reason, 'created_at': item.created_at, 'resolved_at': item.resolved_at, 'resolved_entry_id': item.resolved_entry_id,
        'entry': {'id': entry.pk, 'vehicle_public_id': str(entry.vehicle.public_id), 'plate_number': entry.vehicle.plate_number,
            'model_name': entry.vehicle.model_name, 'partner': entry.partner_id, 'partner_name': entry.partner.name if entry.partner else '',
            'kind': entry.kind, 'entry_date': entry.entry_date, 'odometer_km': entry.odometer_km, 'amount_krw': entry.amount_krw, 'description': entry.description}}

class RecordCorrectionView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        rows = RecordCorrectionRequest.objects.select_related('entry__vehicle', 'entry__partner')
        if request.GET.get('workplace') == '1':
            rows = rows.filter(entry__partner_id__in=verification_partners(request.user), resolved_at__isnull=True,
                entry__vehicle__status='active', entry__vehicle__ownerships__ended_at__isnull=True, entry__vehicle__ownerships__user_id=F('requested_by_id'))
        else: rows = rows.filter(requested_by=request.user, entry__vehicle__in=active_vehicles(request.user))
        return Response([correction_payload(row) for row in rows[:100]])
    @transaction.atomic
    def post(self, request):
        entry_id = serializers.IntegerField(min_value=1).run_validation(request.data.get('entry_id'))
        reason = serializers.CharField(max_length=240, allow_blank=False).run_validation(request.data.get('reason'))
        entry = LedgerEntry.objects.select_for_update(of=('self',)).select_related('vehicle').filter(pk=entry_id, source='partner', vehicle__in=active_vehicles(request.user)).first()
        if entry is None: raise NotFound('본인 차량의 업체 인증 기록만 정정을 요청할 수 있습니다.')
        ownership = entry.vehicle.current_ownership
        if ownership is None or entry.created_at < ownership.started_at: raise PermissionDenied('이전 소유자의 기록은 정정을 요청할 수 없습니다.')
        if entry.corrections.exists(): raise serializers.ValidationError('이미 정정된 원본입니다. 가장 최근 정정 기록을 선택해 주세요.')
        item, created = RecordCorrectionRequest.objects.get_or_create(entry=entry, requested_by=request.user, resolved_at__isnull=True, defaults={'reason': reason})
        return Response(correction_payload(item), status=201 if created else 200)

class ResolveCorrectionView(APIView):
    permission_classes = [IsAuthenticated]
    @transaction.atomic
    def post(self, request, pk):
        item = RecordCorrectionRequest.objects.select_for_update(of=('self',)).select_related('entry__vehicle','entry__partner').filter(pk=pk,
            entry__partner_id__in=verification_partners(request.user), entry__vehicle__status='active', entry__vehicle__ownerships__ended_at__isnull=True,
            entry__vehicle__ownerships__user_id=F('requested_by_id')).first()
        if item is None: raise NotFound('소속 업체의 정정 요청을 찾을 수 없습니다.')
        entry_id = serializers.IntegerField(min_value=1).run_validation(request.data.get('resolved_entry_id'))
        correction = LedgerEntry.objects.filter(pk=entry_id, corrects_id=item.entry_id, vehicle_id=item.entry.vehicle_id, partner_id=item.entry.partner_id, source='partner').first()
        if correction is None: raise serializers.ValidationError({'resolved_entry_id': '원본에 연결된 업체 인증 정정 기록이 필요합니다.'})
        if item.resolved_at and item.resolved_entry_id != entry_id: raise serializers.ValidationError('이미 처리된 요청입니다.')
        item.resolved_entry=correction;item.resolved_at=item.resolved_at or timezone.now();item.save(update_fields=['resolved_entry','resolved_at'])
        return Response(correction_payload(item))
