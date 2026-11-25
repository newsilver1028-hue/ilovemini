from datetime import timedelta, time, datetime
from types import SimpleNamespace
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import TestCase, RequestFactory
from django.utils import timezone
from django.urls import reverse
from core.models import (Partner, PartnerStaff, PartnerBooking, PartnerWeeklySchedule, PartnerScheduleException,
    PartnerPart, PartnerWorkOrder, PartnerWorkOrderLine, PartnerStockMovement, LedgerEntry, Vehicle, VehicleOwnership)
from core.booking_schedule import is_slot_available, available_slots
from core.partner_admin import partner_admin_site, PartnerBookingAdminForm
from core.work_order_admin import PartnerWorkOrderAdmin


class WorkshopAuditTests(TestCase):
    def setUp(self):
        self.partner=Partner.objects.create(name='격리 점검업체',is_active=True)
        self.other=Partner.objects.create(name='다른 점검업체',is_active=True)
        self.worker=get_user_model().objects.create_user('audit-worker')
        self.owner=get_user_model().objects.create_user('audit-owner')
        PartnerStaff.objects.create(user=self.worker,partner=self.partner,is_active=True,can_manage_bookings=True,can_verify_records=True)
        self.vehicle=Vehicle.objects.create(model_name='MINI Cooper S',plate_number='검수5678',current_odometer_km=65432)
        VehicleOwnership.objects.create(user=self.owner,vehicle=self.vehicle)
        self.day=timezone.localdate()+timedelta(days=14)
        self.start=timezone.make_aware(datetime.combine(self.day,time(9)))
        self.client.force_login(self.worker)

    def booking(self, **kwargs):
        return PartnerBooking.objects.create(partner=self.partner,customer=self.owner,vehicle=self.vehicle,
            scheduled_at=self.start,status='confirmed',service_type='검수',**kwargs)

    def test_new_partner_has_seven_days_and_edit_keeps_custom_hours(self):
        self.assertEqual(self.partner.weekly_booking_schedule.count(),7)
        self.assertEqual(PartnerWeeklySchedule.objects.filter(partner=self.partner,opens_at=time(9),closes_at=time(18),is_closed=False).count(),7)
        row=PartnerWeeklySchedule.objects.get(partner=self.partner,weekday=0)
        row.opens_at=time(10);row.save()
        self.partner.description='변경';self.partner.save()
        row.refresh_from_db();self.assertEqual(row.opens_at,time(10))

    def test_two_hour_booking_and_thirty_minute_extension_block_next_slot(self):
        booking=self.booking(duration_minutes=120)
        self.assertFalse(is_slot_available(self.partner,self.start+timedelta(hours=1),60)[0])
        self.assertTrue(is_slot_available(self.partner,self.start+timedelta(hours=2),60)[0])
        booking.duration_minutes=150;booking.save(update_fields=['duration_minutes'])
        self.assertFalse(is_slot_available(self.partner,self.start+timedelta(hours=2),60)[0])
        self.assertTrue(is_slot_available(self.partner,self.start+timedelta(minutes=150),60)[0])
        slots=available_slots(self.partner,self.day,'검수')['slots']
        self.assertNotIn(timezone.localtime(self.start+timedelta(hours=2)).isoformat(),slots)

    def test_closed_and_outside_hours_rejected(self):
        PartnerScheduleException.objects.create(partner=self.partner,date=self.day,is_closed=True)
        self.assertFalse(is_slot_available(self.partner,self.start,60)[0])
        self.assertEqual(available_slots(self.partner,self.day,'검수')['slots'],[])
        PartnerScheduleException.objects.all().delete()
        self.assertFalse(is_slot_available(self.partner,self.start-timedelta(minutes=30),60)[0])
        self.assertFalse(is_slot_available(self.partner,self.start+timedelta(hours=8),120)[0])

    def test_booking_admin_overlap_is_form_error(self):
        first=self.booking(duration_minutes=120)
        second=PartnerBooking.objects.create(partner=self.partner,customer=self.owner,vehicle=self.vehicle,
            scheduled_at=self.start+timedelta(hours=3),status='confirmed',service_type='검수')
        response=self.client.post(reverse('partner_admin:core_partnerbooking_change',args=[second.pk]),{
            'scheduled_at_0':str(self.day),'scheduled_at_1':'10:00:00','duration_minutes':60,
            'status':'confirmed','assigned_resource':'','partner_note':'','_save':'저장'})
        self.assertEqual(response.status_code,200)
        self.assertIn('scheduled_at',response.context['adminform'].form.errors)
        second.refresh_from_db();self.assertEqual(second.scheduled_at,self.start+timedelta(hours=3))

    def test_foreign_workorder_detail_print_and_share_denied(self):
        order=PartnerWorkOrder.objects.create(partner=self.other,plate_number='타업체1234',vehicle_model='비공개 차량',contact_phone='')
        urls=[reverse('partner_admin:core_partnerworkorder_change',args=[order.pk]),
            reverse('partner_admin:partner-workorder-quote',args=[order.pk]),
            reverse('partner_admin:partner-workorder-document',args=[order.pk,'receipt']),
            reverse('partner_admin:partner-workorder-quote-share',args=[order.pk])]
        for url in urls:
            response=self.client.post(url) if 'share' in url else self.client.get(url)
            self.assertIn(response.status_code,[302,403,404])
            self.assertNotIn('비공개 차량',response.content.decode())

    def test_completion_repeated_does_not_duplicate_stock_or_ledger(self):
        booking=self.booking()
        part=PartnerPart.objects.create(partner=self.partner,name='검수 재고',stock_quantity=5)
        order=PartnerWorkOrder.objects.create(partner=self.partner,booking=booking,vehicle=self.vehicle,
            vehicle_model=self.vehicle.model_name,plate_number=self.vehicle.plate_number,odometer_km=65432,status='in_progress')
        PartnerWorkOrderLine.objects.create(work_order=order,kind='part',part=part,description='필터',quantity=2,unit_price_krw=11000)
        PartnerWorkOrderLine.objects.create(work_order=order,kind='labor',description='교환 공임',quantity=1,unit_price_krw=33000)
        request=RequestFactory().post('/partner-admin/');request.user=self.worker;request.session={};request._messages=FallbackStorage(request)
        admin=PartnerWorkOrderAdmin(PartnerWorkOrder,partner_admin_site)
        for _ in range(2):
            order.status='completed'
            form=SimpleNamespace(instance=order,cleaned_data={'booking':booking},save_m2m=lambda:None)
            admin.save_model(request,order,form,True);admin.save_related(request,form,[],True)
        part.refresh_from_db();order.refresh_from_db()
        self.assertEqual(part.stock_quantity,3)
        self.assertEqual(PartnerStockMovement.objects.filter(part=part).count(),1)
        entry=LedgerEntry.objects.get(vehicle=self.vehicle)
        self.assertEqual((entry.amount_krw,entry.odometer_km,order.final_total_krw),(55000,65432,55000))
        self.assertEqual(entry.line_items,[{'name':'필터','amount_krw':22000},{'name':'교환 공임','amount_krw':33000}])

    def test_service_history_excludes_other_shop_and_cancelled_orders(self):
        current=PartnerWorkOrder.objects.create(partner=self.partner,plate_number='검수5678')
        PartnerWorkOrder.objects.create(partner=self.partner,plate_number='검수5678',customer_concern='자업체 이력')
        PartnerWorkOrder.objects.create(partner=self.other,plate_number='검수5678',customer_concern='타업체 비밀')
        PartnerWorkOrder.objects.create(partner=self.partner,plate_number='검수5678',status='cancelled',customer_concern='취소 비밀')
        html=str(PartnerWorkOrderAdmin(PartnerWorkOrder,partner_admin_site).vehicle_service_history(current))
        self.assertIn('자업체 이력',html);self.assertNotIn('타업체 비밀',html);self.assertNotIn('취소 비밀',html)
