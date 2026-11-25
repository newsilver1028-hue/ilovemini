from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient, APIRequestFactory, force_authenticate
from core import test_workshop_audit as fixture
from core.models import PartnerBooking
from core.views import PartnerBookingViewSet


class InputAndBookingStateTests(TestCase):
    setUp = fixture.WorkshopAuditTests.setUp
    booking = fixture.WorkshopAuditTests.booking

    def test_malformed_vehicle_filters_are_400_not_server_errors(self):
        api=APIClient();api.force_authenticate(self.owner)
        for endpoint in ['ledger','reminders']:
            for value in ['abc','0','9223372036854775808']:
                with self.subTest(endpoint=endpoint,value=value):
                    self.assertEqual(api.get('/api/'+endpoint+'/',{'vehicle':value}).status_code,400)
            self.assertEqual(api.get('/api/'+endpoint+'/',{'vehicle':self.vehicle.pk}).status_code,200)

    def test_calendar_boundary_years_are_400_not_server_errors(self):
        for model,field in [('partnerbooking','scheduled_at'),('ledgerentry','entry_date')]:
            url=reverse('partner_admin:core_'+model+'_changelist')
            for year,month in [('0001','1'),('9999','12')]:
                with self.subTest(model=model,year=year):
                    self.assertEqual(self.client.get(url,{field+'__year':year,field+'__month':month}).status_code,400)
            self.assertEqual(self.client.get(url).status_code,200)
        for year in ['0001','9999']:
            self.assertEqual(self.client.get(reverse('partner_admin:partner-operations-report'),{'month':year+'-12'}).status_code,400)
            self.assertEqual(self.client.get('/admin/core/pointtransaction/',{'calendar_year':year}).status_code,400)

    def request(self,action,user,booking,payload):
        request=APIRequestFactory().post('/api/bookings/'+str(booking.pk)+'/'+action+'/',payload,format='json')
        force_authenticate(request,user)
        return request

    def test_stale_confirmation_cannot_resurrect_cancelled_booking(self):
        booking=self.booking();booking.status='requested';booking.save(update_fields=['status'])
        stale=PartnerBooking.objects.get(pk=booking.pk)
        PartnerBooking.objects.filter(pk=booking.pk).update(status='cancelled')
        request=self.request('respond',self.worker,booking,{'status':'confirmed'})
        with patch.object(PartnerBookingViewSet,'get_object',return_value=stale):
            response=PartnerBookingViewSet.as_view({'post':'respond'})(request,pk=booking.pk)
        self.assertEqual(response.status_code,409)
        booking.refresh_from_db();self.assertEqual(booking.status,'cancelled')

    def test_stale_cancellation_cannot_overwrite_completed_booking(self):
        booking=self.booking();stale=PartnerBooking.objects.get(pk=booking.pk)
        PartnerBooking.objects.filter(pk=booking.pk).update(status='completed')
        request=self.request('cancel',self.owner,booking,{'cancellation_reason':'검수'})
        with patch.object(PartnerBookingViewSet,'get_object',return_value=stale):
            response=PartnerBookingViewSet.as_view({'post':'cancel_booking'})(request,pk=booking.pk)
        self.assertEqual(response.status_code,409)
        booking.refresh_from_db();self.assertEqual(booking.status,'completed')

    def test_normal_confirmation_completion_and_cancellation_still_work(self):
        booking=self.booking();booking.status='requested';booking.save(update_fields=['status'])
        api=APIClient();api.force_authenticate(self.worker)
        url='/api/bookings/'+str(booking.pk)+'/respond/'
        self.assertEqual(api.post(url,{'status':'confirmed'},format='json').status_code,200)
        self.assertEqual(api.post(url,{'status':'completed'},format='json').status_code,200)
        self.assertEqual(api.post(url,{'status':'completed'},format='json').status_code,409)
        other=PartnerBooking.objects.create(partner=self.partner,customer=self.owner,vehicle=self.vehicle,scheduled_at=self.start,service_type='취소 검수')
        api.force_authenticate(self.owner)
        self.assertEqual(api.post('/api/bookings/'+str(other.pk)+'/cancel/',{},format='json').status_code,200)
        other.refresh_from_db();self.assertEqual(other.status,'cancelled')
