from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient
from .models import Partner, PartnerStaff, PartnerBooking

class EstimateTests(TestCase):
    def test_revision_and_member_decision(self):
        U=get_user_model()
        owner=U.objects.create_user('estimate-owner')
        worker=U.objects.create_user('estimate-worker')
        other=U.objects.create_user('estimate-other')
        partner=Partner.objects.create(name='견적업체',is_active=True)
        PartnerStaff.objects.create(user=worker,partner=partner,is_active=True,can_manage_bookings=True)
        booking=PartnerBooking.objects.create(customer=owner,partner=partner,scheduled_at=timezone.now(),service_type='정비')
        client=APIClient();client.force_authenticate(worker)
        payload={'booking':booking.pk,'items':[{'title':'오일','amount_krw':100000}]}
        first=client.post('/api/service-estimates/',payload,format='json')
        self.assertEqual(first.status_code,201,first.data)
        self.assertEqual(first.data['total_krw'],100000)
        second=client.post('/api/service-estimates/',payload,format='json')
        self.assertEqual(second.status_code,201,second.data)
        self.assertEqual(second.data['revision'],2)
        url=f"/api/service-estimates/{second.data['id']}/respond/"
        client.force_authenticate(other)
        self.assertEqual(client.post(url,{'decision':'accepted'}).status_code,404)
        client.force_authenticate(owner)
        self.assertEqual(client.post(f"/api/service-estimates/{first.data['id']}/respond/",{'decision':'accepted'}).status_code,400)
        self.assertEqual(client.post(url,{'decision':'accepted'}).status_code,200)
        self.assertEqual(client.post(url,{'decision':'accepted'}).status_code,400)

    def test_recommendation_accept_creates_only_one_reminder(self):
        from .models import Vehicle, VehicleOwnership, LedgerEntry, Reminder
        owner=get_user_model().objects.create_user('reminder-owner')
        worker=get_user_model().objects.create_user('reminder-worker')
        partner=Partner.objects.create(name='권장업체',is_active=True)
        PartnerStaff.objects.create(user=worker,partner=partner,is_active=True,can_verify_records=True)
        vehicle=Vehicle.objects.create(model_name='MINI')
        VehicleOwnership.objects.create(vehicle=vehicle,user=owner)
        entry=LedgerEntry.objects.create(vehicle=vehicle,partner=partner,source='partner',kind='service')
        client=APIClient();client.force_authenticate(worker)
        response=client.post('/api/maintenance-recommendations/',{'entry':entry.pk,'title':'오일 교체','due_odometer_km':20000},format='json')
        self.assertEqual(response.status_code,201,response.data)
        self.assertFalse(Reminder.objects.exists())
        client.force_authenticate(owner)
        url=f"/api/maintenance-recommendations/{response.data['id']}/respond/"
        self.assertEqual(client.post(url,{'decision':'accepted'}).status_code,200)
        self.assertEqual(client.post(url,{'decision':'accepted'}).status_code,400)
        self.assertEqual(Reminder.objects.count(),1)

    def test_admin_creation_forms_render(self):
        user=get_user_model().objects.create_superuser('phase-admin','admin@example.test','test-pass')
        self.client.force_login(user)
        for model in ['serviceestimate','maintenancerecommendation']:
            response=self.client.get(f'/admin/core/{model}/add/')
            self.assertEqual(response.status_code,200)
