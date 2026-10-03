from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.core.cache import cache
from django.utils import timezone
from rest_framework.test import APIClient
from .models import Vehicle, VehicleOwnership, VehiclePlateHistory, Partner, PartnerStaff, PartnerBooking, LedgerEntry, Reminder
from .member_roles import assign_member_grade, member_grade

User=get_user_model()
class PermissionAuditTests(TestCase):
    def setUp(self):
        cache.clear()
        self.owner=User.objects.create_user(username='owner')
        self.other=User.objects.create_user(username='other')
        self.staff=User.objects.create_user(username='editor',is_staff=True)
        self.root=User.objects.create_user(username='root',is_staff=True,is_superuser=True)
        self.car=Vehicle.objects.create(model_name='MINI',plate_number='12가3456')
        VehicleOwnership.objects.create(vehicle=self.car,user=self.owner)
    def client_for(self,user):
        c=APIClient();c.force_authenticate(user);return c
    def test_member_cannot_promote_self(self):
        with self.assertRaises(PermissionDenied):assign_member_grade(self.other,self.other,'mini')
    def test_operator_can_assign_mini(self):
        self.assertEqual(assign_member_grade(self.root,self.other,'mini'),'mini')
    def test_demotion_disables_partner_access(self):
        p=Partner.objects.create(name='shop',is_active=True)
        m=PartnerStaff.objects.create(user=self.other,partner=p,is_active=True,can_verify_records=True)
        self.assertEqual(member_grade(self.other),'partner')
        assign_member_grade(self.root,self.other,'general');m.refresh_from_db()
        self.assertFalse(m.is_active)
    def test_other_member_cannot_get_vehicle(self):
        self.assertEqual(self.client_for(self.other).get(f'/api/vehicles/{self.car.pk}/').status_code,404)
    def test_content_staff_cannot_get_other_vehicle(self):
        self.assertEqual(self.client_for(self.staff).get(f'/api/vehicles/{self.car.pk}/').status_code,404)
    def test_plate_history_cannot_be_deleted_in_admin(self):
        row=VehiclePlateHistory.objects.create(vehicle=self.car,plate_number=self.car.plate_number)
        r=RequestFactory().get('/admin/');r.user=self.root
        self.assertFalse(admin.site._registry[VehiclePlateHistory].has_delete_permission(r,row))
    def test_inactive_shop_cannot_respond_even_to_own_booking(self):
        shop=Partner.objects.create(name='inactive',is_active=False)
        PartnerStaff.objects.create(user=self.other,partner=shop,is_active=True,can_manage_bookings=True)
        b=PartnerBooking.objects.create(customer=self.other,partner=shop,scheduled_at=timezone.now(),service_type='service')
        response=self.client_for(self.other).post(f'/api/bookings/{b.pk}/respond/',{'status':'confirmed'},format='json')
        self.assertIn(response.status_code,[403,404])

    def test_content_staff_cannot_read_ledger_or_reminder(self):
        entry=LedgerEntry.objects.create(vehicle=self.car,kind='service')
        reminder=Reminder.objects.create(vehicle=self.car,title='private')
        c=self.client_for(self.staff)
        self.assertEqual(c.get(f'/api/ledger/{entry.pk}/').status_code,404)
        self.assertEqual(c.get(f'/api/reminders/{reminder.pk}/').status_code,404)
    def test_superuser_can_read_vehicle_and_plate_delete_action_absent(self):
        self.assertEqual(self.client_for(self.root).get(f'/api/vehicles/{self.car.pk}/').status_code,200)
        r=RequestFactory().get('/admin/');r.user=self.root
        self.assertNotIn('delete_selected',admin.site._registry[VehiclePlateHistory].get_actions(r))
