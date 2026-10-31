from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from .member_roles import member_grade
from .models import Partner, PartnerStaff


class MemberGradeAdminActionTests(TestCase):
    def setUp(self):
        self.operator = get_user_model().objects.create_superuser(
            username="grade-operator", email="operator@example.test", password="unused",
        )
        self.member = get_user_model().objects.create_user(
            username="grade-member", email="member@example.test",
        )
        self.client = Client()
        self.client.force_login(self.operator)
        self.url = reverse("admin:auth_user_changelist")

    def apply_grade(self, grade):
        return self.client.post(self.url, {
            "action": f"set_grade_{grade}",
            "_selected_action": [str(self.member.pk)],
            "index": "0",
        }, follow=True)

    def test_partner_grade_action_assigns_company_permissions_and_demotes(self):
        partner = Partner.objects.create(name="테스트 정비업체", is_active=True)
        other_partner = Partner.objects.create(name="기존 연결 업체", is_active=True)
        PartnerStaff.objects.create(
            user=self.member, partner=other_partner, is_active=True,
            can_manage_bookings=True,
        )
        response = self.apply_grade("partner")
        self.assertContains(response, "소속 업체")
        self.assertContains(response, "협력업체 등급 적용")

        response = self.client.post(self.url, {
            "action": "set_grade_partner",
            "_selected_action": [str(self.member.pk)],
            "index": "0",
            "confirm_partner_assignment": "1",
            "partner": str(partner.pk),
            "can_manage_bookings": "on",
            "can_verify_records": "on",
        }, follow=True)
        self.member.refresh_from_db()
        self.assertEqual(member_grade(self.member), "partner")
        membership = PartnerStaff.objects.get(user=self.member, partner=partner)
        self.assertEqual(membership.partner, partner)
        self.assertTrue(membership.is_active)
        self.assertTrue(membership.can_manage_bookings)
        self.assertTrue(membership.can_verify_records)
        self.assertFalse(PartnerStaff.objects.get(user=self.member, partner=other_partner).is_active)
        self.assertEqual(
            list(PartnerStaff.objects.filter(user=self.member, is_active=True).values_list("partner_id", flat=True)),
            [partner.pk],
        )
        self.assertContains(response, "1명의 회원 등급을 협력업체(으)로 변경했습니다.")

        response = self.apply_grade("general")
        self.member.refresh_from_db()
        self.assertEqual(member_grade(self.member), "general")
        self.assertFalse(PartnerStaff.objects.get(user=self.member, partner=partner).is_active)
        self.assertContains(response, "1명의 회원 등급을 일반회원(으)로 변경했습니다.")

    def test_partner_assignment_does_not_grant_an_inactive_partner(self):
        inactive_partner = Partner.objects.create(name="중단 업체", is_active=False)
        response = self.client.post(self.url, {
            "action": "set_grade_partner",
            "_selected_action": [str(self.member.pk)],
            "index": "0",
        }, follow=True)
        self.assertContains(response, "협력업체 등급 적용")
        response = self.client.post(self.url, {
            "action": "set_grade_partner",
            "_selected_action": [str(self.member.pk)],
            "index": "0",
            "confirm_partner_assignment": "1",
            "partner": str(inactive_partner.pk),
        }, follow=True)
        self.assertContains(response, "선택가능항목에 없습니다")
        self.assertEqual(member_grade(self.member), "general")
        self.assertFalse(PartnerStaff.objects.filter(user=self.member).exists())
