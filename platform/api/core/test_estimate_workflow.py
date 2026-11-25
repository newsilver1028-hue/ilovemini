from types import SimpleNamespace
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone
from core.models import Partner, PartnerStaff, Vehicle, VehicleOwnership, PartnerBooking, ServiceEstimate, PartnerWorkOrder, LedgerEntry
from core.partner_admin import partner_admin_site
from core.phase_one_admin import EstimateAdmin
from core.work_order_admin import PartnerWorkOrderAdmin
from core.serializers import LedgerEntrySerializer


class EstimateWorkflowTests(TestCase):
    """Isolated database fixtures; no push devices, phones or real customers."""
    def setUp(self):
        User = get_user_model()
        self.worker = User.objects.create_user('qa-worker')
        self.owner = User.objects.create_user('qa-owner')
        self.partner = Partner.objects.create(name='검수용 업체', is_active=True)
        PartnerStaff.objects.create(user=self.worker, partner=self.partner, is_active=True, can_manage_bookings=True, can_verify_records=True)
        self.vehicle = Vehicle.objects.create(model_name='MINI Cooper S', plate_number='검수1234', current_odometer_km=60000)
        VehicleOwnership.objects.create(user=self.owner, vehicle=self.vehicle)
        self.booking = PartnerBooking.objects.create(partner=self.partner, customer=self.owner, vehicle=self.vehicle, scheduled_at=timezone.now(), status='confirmed', contact_phone='', service_type='검수 정비')
        self.items = [{'title': '엔진오일·필터', 'amount_krw': 110000}, {'title': '브레이크 점검', 'amount_krw': 44000}]
        self.estimate = ServiceEstimate.objects.create(booking=self.booking, items=self.items, total_krw=154000, status='accepted')

    def request(self):
        request = RequestFactory().post('/partner-admin/core/serviceestimate/', {'convert_estimate':str(self.estimate.pk)})
        request.user = self.worker
        request.session = {}
        request._messages = FallbackStorage(request)
        return request

    def test_convert_complete_and_customer_receipt_preserve_values(self):
        estimate_admin = EstimateAdmin(ServiceEstimate, partner_admin_site)
        response = estimate_admin.changelist_view(self.request())
        order = PartnerWorkOrder.objects.get(booking=self.booking)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(order.vehicle_id, self.vehicle.pk)
        self.assertEqual((order.vehicle_model, order.plate_number, order.odometer_km), ('MINI Cooper S', '검수1234', 60000))
        self.assertEqual(order.quoted_total_krw, 154000)
        self.assertEqual([(line.description,line.amount_krw) for line in order.lines.all()], [('엔진오일·필터',110000),('브레이크 점검',44000)])
        again = estimate_admin.changelist_view(self.request())
        self.assertEqual(again['Location'], response['Location'])
        self.assertEqual(PartnerWorkOrder.objects.count(), 1)
        self.estimate.booking.refresh_from_db()
        self.assertIn('작업지시 열기', str(estimate_admin.work_order_button(self.estimate)))
        form = SimpleNamespace(instance=order, cleaned_data={'booking':self.booking}, save_m2m=lambda:None)
        order.status = PartnerWorkOrder.Status.COMPLETED
        admin = PartnerWorkOrderAdmin(PartnerWorkOrder, partner_admin_site)
        admin.save_model(self.request(), order, form, True)
        admin.save_related(self.request(), form, [], True)
        order.refresh_from_db()
        entry = LedgerEntry.objects.get(vehicle=self.vehicle)
        self.assertEqual((entry.odometer_km,entry.amount_krw,order.final_total_krw), (60000,154000,154000))
        self.assertEqual(entry.line_items, [{'name':'엔진오일·필터','amount_krw':110000},{'name':'브레이크 점검','amount_krw':44000}])
        serialized = LedgerEntrySerializer(entry).data
        self.assertEqual(serialized['amount_krw'],154000)
        self.assertEqual([(item['name'], item['amount_krw']) for item in serialized['line_items']], [(item['name'], item['amount_krw']) for item in entry.line_items])
        form._previous_status = PartnerWorkOrder.Status.COMPLETED
        admin.save_related(self.request(), form, [], True)
        self.assertEqual(LedgerEntry.objects.count(),1)

    def test_another_partner_cannot_convert_estimate(self):
        stranger = get_user_model().objects.create_user('qa-stranger')
        other = Partner.objects.create(name='다른 검수업체', is_active=True)
        PartnerStaff.objects.create(user=stranger,partner=other,is_active=True,can_manage_bookings=True)
        self.client.force_login(stranger)
        response = self.client.post(reverse('partner_admin:core_serviceestimate_changelist'), {'convert_estimate':str(self.estimate.pk)})
        self.assertEqual(response.status_code,404)
        self.assertFalse(PartnerWorkOrder.objects.exists())
