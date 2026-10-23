from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from .models import MaintenanceRecommendation, ServiceEstimate, Reminder, PartnerStaff, VehicleOwnership

class RecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaintenanceRecommendation
        fields = ['id','entry','member','title','due_date','due_odometer_km','status','reminder','created_at','responded_at']
        read_only_fields = ['member','status','reminder','created_at','responded_at']

    def validate(self, data):
        entry = data['entry']
        if not self.context['request'].user.is_superuser and not PartnerStaff.objects.filter(user=self.context['request'].user, partner=entry.partner, is_active=True, can_verify_records=True, partner__is_active=True).exists():
            raise PermissionDenied('해당 업체 정비 기록의 담당자만 권장 알림을 작성할 수 있습니다.')
        if entry.source != 'partner' or not (data.get('due_date') or data.get('due_odometer_km') is not None):
            raise ValidationError('업체 인증 기록과 교체일 또는 주행거리가 필요합니다.')
        return data

class RecommendationViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = RecommendationSerializer

    def get_queryset(self):
        return MaintenanceRecommendation.objects.filter(member=self.request.user).order_by('-created_at')

    def list(self, request):
        return Response(self.get_serializer(self.get_queryset(), many=True).data)

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        entry = serializer.validated_data['entry']
        ownership = get_object_or_404(VehicleOwnership, vehicle=entry.vehicle, ended_at__isnull=True)
        serializer.save(member=ownership.user)
        return Response(serializer.data, status=201)

    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        decision = request.data.get('decision')
        if decision not in ['accepted','declined']:
            raise ValidationError('accepted 또는 declined를 선택해 주세요.')
        with transaction.atomic():
            row = get_object_or_404(self.get_queryset().select_for_update(), pk=pk)
            if row.status != 'pending':
                raise ValidationError('이미 응답한 권장 알림입니다.')
            if not VehicleOwnership.objects.filter(vehicle=row.entry.vehicle, user=request.user, ended_at__isnull=True).exists():
                raise PermissionDenied('현재 차량 회원만 응답할 수 있습니다.')
            if decision == 'accepted':
                row.reminder = Reminder.objects.create(vehicle=row.entry.vehicle, title=row.title, due_date=row.due_date, due_odometer_km=row.due_odometer_km)
            row.status = decision
            row.responded_at = timezone.now()
            row.save()
        return Response(self.get_serializer(row).data)

class EstimateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceEstimate
        validators = []
        fields = ['id','booking','revision','items','total_krw','note','status','created_at','responded_at']
        read_only_fields = ['revision','total_krw','status','created_at','responded_at']

    def validate(self, data):
        booking = data['booking']
        if not self.context['request'].user.is_superuser and not PartnerStaff.objects.filter(user=self.context['request'].user, partner=booking.partner, is_active=True, can_manage_bookings=True, partner__is_active=True).exists():
            raise PermissionDenied('해당 업체 예약 담당자만 견적을 작성할 수 있습니다.')
        if booking.status not in ['requested','confirmed']:
            raise ValidationError('진행 가능한 예약에만 견적을 작성할 수 있습니다.')
        items = data.get('items')
        if not isinstance(items,list) or not 1 <= len(items) <= 50:
            raise ValidationError('견적 항목을 1~50개 입력해 주세요.')
        for item in items:
            if not isinstance(item,dict) or not isinstance(item.get('title'),str) or not item['title'].strip() or len(item['title'])>160 or type(item.get('amount_krw')) is not int or not 0 <= item['amount_krw'] <= 100000000:
                raise ValidationError('각 항목의 작업명과 올바른 금액을 입력해 주세요.')
        return data

class EstimateViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = EstimateSerializer

    def get_queryset(self):
        return ServiceEstimate.objects.filter(booking__customer=self.request.user).exclude(status='draft').order_by('-created_at')

    def list(self, request):
        return Response(self.get_serializer(self.get_queryset(), many=True).data)

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        from .models import PartnerBooking
        with transaction.atomic():
            booking = PartnerBooking.objects.select_for_update().get(pk=serializer.validated_data['booking'].pk)
            last = ServiceEstimate.objects.filter(booking=booking).order_by('-revision').first()
            ServiceEstimate.objects.filter(booking=booking, status='sent').update(status='superseded')
            serializer.save(revision=last.revision+1 if last else 1, status='sent', total_krw=sum(item['amount_krw'] for item in serializer.validated_data['items']))
        return Response(serializer.data, status=201)

    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        decision = request.data.get('decision')
        if decision not in ['accepted','declined']:
            raise ValidationError('accepted 또는 declined를 선택해 주세요.')
        from .models import PartnerBooking
        with transaction.atomic():
            row = get_object_or_404(self.get_queryset(), pk=pk)
            booking = PartnerBooking.objects.select_for_update().get(pk=row.booking_id)
            row.refresh_from_db()
            if booking.status not in ['requested','confirmed'] or row.status != 'sent':
                raise ValidationError('현재 응답할 수 없는 견적입니다.')
            row.status = decision
            row.responded_at = timezone.now()
            row.save(update_fields=['status','responded_at'])
        return Response(self.get_serializer(row).data)
