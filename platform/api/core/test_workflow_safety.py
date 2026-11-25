import hashlib,json,io,re
from types import SimpleNamespace
from unittest.mock import patch
from datetime import timedelta
from django.test import TestCase,RequestFactory
from django.urls import reverse
from django.utils import timezone
from django.contrib.messages.storage.fallback import FallbackStorage
from openpyxl import load_workbook
from core import test_workshop_audit as fixture
from core.models import (PartnerWorkOrder,PartnerWorkOrderLine,PartnerPart,PartnerStockMovement,LedgerEntry,
    PartnerPosIntegration,PartnerPayment,PartnerDailyClose,PartnerWeeklySchedule)
from core.work_order_admin import PartnerWorkOrderAdmin
from core.partner_admin import partner_admin_site


class WorkflowSafetyTests(TestCase):
    setUp=fixture.WorkshopAuditTests.setUp
    booking=fixture.WorkshopAuditTests.booking

    def request(self):
        request=RequestFactory().post('/partner-admin/');request.user=self.worker;request.session={};request._messages=FallbackStorage(request)
        return request

    def completion(self,stock=0):
        booking=self.booking();part=PartnerPart.objects.create(partner=self.partner,name='검수 부품',stock_quantity=stock)
        order=PartnerWorkOrder.objects.create(partner=self.partner,booking=booking,vehicle=self.vehicle,status='in_progress')
        PartnerWorkOrderLine.objects.create(work_order=order,part=part,kind='part',description='필터',quantity=1,unit_price_krw=100000)
        form=SimpleNamespace(instance=order,cleaned_data={'booking':booking},save_m2m=lambda:None)
        return order,part,form

    def test_insufficient_stock_preserves_status_and_has_no_ledger_or_movement(self):
        order,part,form=self.completion();admin=PartnerWorkOrderAdmin(PartnerWorkOrder,partner_admin_site)
        order.status='completed';admin.save_model(self.request(),order,form,True);admin.save_related(self.request(),form,[],True)
        order.refresh_from_db();part.refresh_from_db()
        self.assertEqual((order.status,order.completed_at,part.stock_quantity),('in_progress',None,0))
        self.assertFalse(PartnerStockMovement.objects.filter(work_order=order).exists())
        self.assertFalse(LedgerEntry.objects.filter(vehicle=self.vehicle).exists())

    def test_unexpected_completion_error_rolls_back_whole_transaction(self):
        from django.db import transaction
        order,part,form=self.completion(stock=5);admin=PartnerWorkOrderAdmin(PartnerWorkOrder,partner_admin_site)
        with self.assertRaises(RuntimeError):
            with transaction.atomic(),patch.object(admin,'create_completion_record',side_effect=RuntimeError('injected QA failure')):
                order.status='completed';admin.save_model(self.request(),order,form,True);admin.save_related(self.request(),form,[],True)
        order.refresh_from_db();part.refresh_from_db()
        self.assertEqual((order.status,part.stock_quantity),('in_progress',5))
        self.assertFalse(PartnerStockMovement.objects.filter(work_order=order).exists())

    def test_quote_reissue_and_edit_revoke_previous_approval(self):
        order=PartnerWorkOrder.objects.create(partner=self.partner,quoted_total_krw=100000)
        url=reverse('partner_admin:partner-workorder-quote-share',args=[order.pk])
        first=self.client.post(url).json()['url'];second=self.client.post(url).json()['url']
        self.assertEqual(self.client.get(first).status_code,404)
        self.client.post(second,{'decision':'approved'});order.refresh_from_db();self.assertEqual(order.quote_status,'approved')
        # Internal technician notes do not alter an accepted quote.
        admin=PartnerWorkOrderAdmin(PartnerWorkOrder,partner_admin_site)
        form=SimpleNamespace(instance=order,cleaned_data={'booking':None},save_m2m=lambda:None)
        order.work_notes='내부 메모';admin.save_model(self.request(),order,form,True);admin.save_related(self.request(),form,[],True)
        order.refresh_from_db();self.assertEqual(order.quote_status,'approved')
        order.customer_concern='고객 요청 변경';admin.save_model(self.request(),order,form,True);admin.save_related(self.request(),form,[],True)
        order.refresh_from_db();self.assertEqual(order.quote_status,'draft');self.assertEqual(self.client.get(second).status_code,404)
        third=self.client.post(url).json()['url'];self.client.post(third,{'decision':'approved'})
        order.refresh_from_db();self.assertEqual(order.quote_status,'approved')

    def test_partial_refund_rejected_and_full_refund_preserves_historical_sales(self):
        token='qa-no-real-provider';PartnerPosIntegration.objects.create(partner=self.partner,provider_name='QA',is_active=True,token_hash=hashlib.sha256(token.encode()).hexdigest())
        order=PartnerWorkOrder.objects.create(partner=self.partner,paid_amount_krw=5000,final_total_krw=105000)
        yesterday=timezone.now()-timedelta(days=1)
        oldclose=PartnerDailyClose.objects.create(partner=self.partner,business_date=timezone.localdate(yesterday),counted_card_krw=100000)
        todayclose=PartnerDailyClose.objects.create(partner=self.partner,business_date=timezone.localdate())
        def post(event):return self.client.post('/api/partner-pos/events/',json.dumps(event),content_type='application/json',HTTP_AUTHORIZATION='Bearer '+token)
        approval={'event_id':'qa-sale','work_order_id':order.pk,'status':'approved','amount_krw':100000,'method':'card','paid_at':yesterday.isoformat()}
        self.assertEqual(post(approval).status_code,200)
        for key in ['amount_krw','cancelled_amount_krw']:
            self.assertEqual(post({'event_id':'qa-sale','work_order_id':order.pk,'status':'cancelled',key:30000}).status_code,400)
        payment=PartnerPayment.objects.get(work_order=order);payment.refresh_from_db();order.refresh_from_db()
        self.assertEqual((payment.status,payment.cancelled_amount_krw,order.paid_amount_krw),('approved',0,105000))
        cancel={'event_id':'qa-sale','work_order_id':order.pk,'status':'cancelled','amount_krw':100000}
        self.assertEqual(post(cancel).status_code,200);self.assertTrue(post(cancel).json()['duplicate'])
        order.refresh_from_db();oldclose.refresh_from_db();todayclose.refresh_from_db()
        self.assertEqual(order.paid_amount_krw,5000)
        self.assertEqual((oldclose.expected_card_krw,oldclose.counted_card_krw,todayclose.expected_refund_krw),(100000,100000,100000))

    def test_stale_workorder_form_cannot_overwrite_another_save(self):
        order=PartnerWorkOrder.objects.create(partner=self.partner,status='received')
        version=order.updated_at.isoformat()
        url=reverse('partner_admin:core_partnerworkorder_change',args=[order.pk])
        screen=self.client.get(url)
        version=re.search(r'name="_work_order_version" value="([^"]+)"',screen.content.decode()).group(1)
        data={'partner':self.partner.pk,'status':'received','quoted_total_krw':0,'final_total_krw':0,'paid_amount_krw':0,
              'quote_revision':0,'lines-TOTAL_FORMS':0,'lines-INITIAL_FORMS':0,'payments-TOTAL_FORMS':0,'payments-INITIAL_FORMS':0,
              '_work_order_version':version,'_save':'저장'}
        first=self.client.post(url,{**data,'work_notes':'첫 담당자 기록'})
        self.assertEqual(first.status_code,302,getattr(first,'context',None) and first.context['adminform'].form.errors)
        second=self.client.post(url,{**data,'work_notes':'','technician_name':'두번째 담당자'})
        self.assertEqual(second.status_code,200)
        self.assertContains(second,'다른 화면에서 변경')
        order.refresh_from_db();self.assertEqual(order.work_notes,'첫 담당자 기록');self.assertEqual(order.technician_name,'')

    def test_stale_booking_form_rejected(self):
        booking=self.booking();version=booking.updated_at.isoformat();url=reverse('partner_admin:core_partnerbooking_change',args=[booking.pk])
        screen=self.client.get(url)
        version=re.search(r'name="_booking_version" value="([^"]+)"',screen.content.decode()).group(1)
        data={'scheduled_at_0':str(self.day),'scheduled_at_1':'09:00:00','duration_minutes':60,'status':'confirmed','assigned_resource':'',
              '_booking_version':version,'_save':'저장'}
        self.assertEqual(self.client.post(url,{**data,'partner_note':'첫 담당자 기록'}).status_code,302)
        response=self.client.post(url,{**data,'partner_note':'덮어쓰기'})
        self.assertEqual(response.status_code,200);self.assertContains(response,'다른 화면에서 변경')
        booking.refresh_from_db();self.assertEqual(booking.partner_note,'첫 담당자 기록')

    def test_export_accepts_closed_days_with_no_opening_times(self):
        PartnerWeeklySchedule.objects.filter(partner=self.partner,weekday=0).update(is_closed=True,opens_at=None,closes_at=None)
        response=self.client.get(reverse('partner_admin:partner-workshop-export'))
        self.assertEqual(response.status_code,200)
        workbook=load_workbook(io.BytesIO(response.content),read_only=True)
        self.assertEqual(len(list(workbook['주간일정'].values)),8)

    def test_fixture_restore_does_not_queue_customer_notifications(self):
        from core.phase_one_notifications import notify_member
        from core.models import ServiceEstimate
        with patch('core.phase_one_notifications.transaction.on_commit') as enqueue:
            notify_member(sender=ServiceEstimate,instance=object(),created=True,raw=True)
        enqueue.assert_not_called()
