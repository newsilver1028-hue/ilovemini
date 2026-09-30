from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from rest_framework.test import APIClient
from .member_roles import GRADES, assign_member_grade, member_grade
from .models import Partner, PartnerStaff

User = get_user_model()


class MemberGradeTests(TestCase):
    def setUp(self):
        self.operator = User.objects.create_user('operator', is_staff=True, is_superuser=True)
        self.member = User.objects.create_user('member')

    def test_three_member_grades_keep_admin_permissions_separate(self):
        self.assertEqual(member_grade(self.member), 'general')
        self.assertEqual(assign_member_grade(self.operator, self.member, 'mini'), 'mini')
        with self.assertRaises(ValidationError):
            assign_member_grade(self.operator, self.member, 'partner')
        shop = Partner.objects.create(name='shop', is_active=True)
        PartnerStaff.objects.create(user=self.member, partner=shop)
        self.assertEqual(assign_member_grade(self.operator, self.member, 'partner'), 'partner')
        self.assertFalse(self.member.is_staff)
        self.assertEqual(set(GRADES), {'general', 'mini', 'partner'})
        with self.assertRaises(ValidationError):
            assign_member_grade(self.operator, self.member, 'staff')
        with self.assertRaises(ValidationError):
            assign_member_grade(self.operator, self.member, 'operator')
        self.assertTrue(self.operator.is_superuser)
        self.assertEqual(assign_member_grade(self.operator, self.member, 'general'), 'general')
        self.assertFalse(PartnerStaff.objects.get(user=self.member).is_active)

    def test_staff_and_members_cannot_change_membership_grades(self):
        for staff in (False, True):
            self.member.is_staff = staff
            self.member.save()
            with self.assertRaises(PermissionDenied):
                assign_member_grade(self.member, self.member, 'mini')
        self.assertEqual(assign_member_grade(self.operator, self.operator, 'general'), 'general')

    def test_profile_is_authenticated_read_only_and_scoped(self):
        client = APIClient()
        self.assertEqual(client.get('/api/me/grade/').status_code, 401)
        shop = Partner.objects.create(name='own shop', is_active=True)
        other = Partner.objects.create(name='other shop', is_active=True)
        PartnerStaff.objects.create(user=self.member, partner=shop)
        PartnerStaff.objects.create(user=self.operator, partner=other)
        client.force_authenticate(self.member)
        result = client.get('/api/me/grade/')
        self.assertEqual(result.data['grade_label'], '협력업체')
        self.assertEqual(result.data['partner_ids'], [shop.pk])
        self.assertEqual(client.post('/api/me/grade/', {'grade': 'operator'}).status_code, 405)
        self.assertEqual(member_grade(self.member), 'partner')
