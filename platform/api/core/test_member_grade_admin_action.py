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

    def test_apply_reports_missing_partner_assignment_then_succeeds_and_demotes(self):
        response = self.apply_grade("partner")
        self.member.refresh_from_db()
        self.assertEqual(member_grade(self.member), "general")
        self.assertContains(response, "협력업체 담당자 관리")
        self.assertContains(response, "조건을 충족하지 않아 변경하지 않았습니다")

        partner = Partner.objects.create(name="테스트 정비업체", is_active=True)
        PartnerStaff.objects.create(
            user=self.member, partner=partner, is_active=True,
            can_manage_bookings=True,
        )
        response = self.apply_grade("partner")
        self.member.refresh_from_db()
        self.assertEqual(member_grade(self.member), "partner")
        self.assertContains(response, "1명의 회원 등급을 협력업체(으)로 변경했습니다.")

        response = self.apply_grade("general")
        self.member.refresh_from_db()
        self.assertEqual(member_grade(self.member), "general")
        self.assertFalse(PartnerStaff.objects.get(user=self.member).is_active)
        self.assertContains(response, "1명의 회원 등급을 일반회원(으)로 변경했습니다.")
