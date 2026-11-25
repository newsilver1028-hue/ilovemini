from decimal import Decimal
from django.test import TestCase, RequestFactory
from django.urls import reverse
from core import test_workshop_audit as workshop_audit
from core.models import PartnerServicePreset, PartnerPart, PartnerWorkOrder, PartnerWorkOrderLine, PartnerQuoteShare
from core.work_order_admin import PartnerWorkOrderLineForm


class ThreeAuditRegressionTests(TestCase):
    setUp = workshop_audit.WorkshopAuditTests.setUp
    booking = workshop_audit.WorkshopAuditTests.booking

    def test_quote_share_with_decimal_quantity_is_public_and_preserves_snapshot(self):
        order=PartnerWorkOrder.objects.create(partner=self.partner,vehicle_model='MINI Cooper S',plate_number='검수5678')
        PartnerWorkOrderLine.objects.create(work_order=order,description='진단 공임',quantity=Decimal('1.50'),unit_price_krw=22000)
        response=self.client.post(reverse('partner_admin:partner-workorder-quote-share',args=[order.pk]))
        self.assertEqual(response.status_code,200,response.content[:300])
        share=PartnerQuoteShare.objects.get(work_order=order)
        self.assertEqual(share.snapshot['items'][0]['quantity'],'1.50')
        self.assertEqual(share.snapshot['items'][0]['amount_krw'],33000)
        self.assertEqual(share.snapshot['total_krw'],33000)
        self.client.logout()
        public=self.client.get(response.json()['url'])
        self.assertEqual(public.status_code,200)
        self.assertContains(public,'진단 공임')
        self.assertContains(public,'33,000')

    def preset_form(self,part=None,**kwargs):
        preset=PartnerServicePreset.objects.create(partner=self.partner,name='필터 교환',kind='part',part=part,default_quantity=2,default_price_krw=11000)
        order=PartnerWorkOrder.objects.create(partner=self.partner)
        request=RequestFactory().post('/partner-admin/');request.user=self.worker
        return PartnerWorkOrderLineForm(data={'preset':preset.pk,'kind':'labor','description':'','quantity':'','unit_price_krw':'','sort_order':0,**kwargs},request=request,parent=order)

    def test_preset_supplies_required_fields_and_linked_part_without_reentry(self):
        part=PartnerPart.objects.create(partner=self.partner,name='필터',stock_quantity=10)
        form=self.preset_form(part)
        self.assertTrue(form.is_valid(),form.errors)
        line=form.save(commit=False)
        self.assertEqual((line.part_id,line.description,line.quantity,line.unit_price_krw,line.kind),(part.pk,'필터 교환',Decimal(2),11000,'part'))

    def test_inactive_preset_part_cannot_be_used(self):
        part=PartnerPart.objects.create(partner=self.partner,name='비활성 필터',stock_quantity=10,is_active=False)
        form=self.preset_form(part)
        self.assertFalse(form.is_valid())
        self.assertIn('preset',form.errors)

    def test_missing_part_is_still_required_for_part_preset(self):
        form=self.preset_form()
        self.assertFalse(form.is_valid())
        self.assertIn('part',form.errors)

    def test_booking_duration_invalid_values_rejected_and_valid_extension_saved(self):
        booking=self.booking()
        url=reverse('partner_admin:core_partnerbooking_change',args=[booking.pk])
        data={'scheduled_at_0':str(self.day),'scheduled_at_1':'09:00:00','status':'confirmed','assigned_resource':'','partner_note':'','_save':'저장'}
        for value in [0,1,31,481]:
            with self.subTest(duration=value):
                response=self.client.post(url,{**data,'duration_minutes':value,'_booking_version':booking.updated_at.isoformat()})
                self.assertEqual(response.status_code,200)
                self.assertIn('duration_minutes',response.context['adminform'].form.errors)
                booking.refresh_from_db();self.assertEqual(booking.duration_minutes,60)
        for value in [30,90,480]:
            response=self.client.post(url,{**data,'duration_minutes':value,'_booking_version':booking.updated_at.isoformat()})
            self.assertEqual(response.status_code,302)
            booking.refresh_from_db();self.assertEqual(booking.duration_minutes,value)
