from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password, make_password
from django.test import TestCase
from rest_framework.test import APIClient

from .member_roles import member_grade
from .models import AppReviewAccount, NaverIdentity, VehicleOwnership


class AppReviewLoginTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = "/api/auth/review-login/"
        self.password = "a-strong-review-password"
        self.account = AppReviewAccount.objects.create(
            username="app-review-demo", password_hash=make_password(self.password), is_active=True,
        )

    def test_login_creates_isolated_general_member_with_sample_vehicle(self):
        response = self.client.post(self.url, {
            "username": self.account.username, "password": self.password,
        }, format="json")
        self.assertEqual(response.status_code, 200)
        self.account.refresh_from_db()
        demo_user = self.account.user
        self.assertEqual(demo_user.username, "app-review-demo")
        self.assertFalse(demo_user.is_staff)
        self.assertFalse(demo_user.is_superuser)
        self.assertEqual(member_grade(demo_user), "general")
        self.assertFalse(NaverIdentity.objects.filter(user=demo_user).exists())
        ownership = VehicleOwnership.objects.get(user=demo_user, ended_at__isnull=True)
        self.assertEqual(ownership.vehicle.model_name, "MINI Cooper S")
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_wrong_password_and_disabled_account_are_rejected(self):
        response = self.client.post(self.url, {"username": self.account.username, "password": "wrong"}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(get_user_model().objects.filter(username=self.account.username).exists())
        self.account.is_active = False
        self.account.save(update_fields=["is_active"])
        response = self.client.post(self.url, {"username": self.account.username, "password": self.password}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_admin_can_create_account_and_password_hash_is_not_exposed(self):
        admin_user = get_user_model().objects.create_superuser("admin", password="admin-password")
        self.client.force_login(admin_user)
        response = self.client.get("/admin/core/appreviewaccount/add/")
        self.assertEqual(response.status_code, 200)
        response = self.client.post("/admin/core/appreviewaccount/add/", {
            "username": "reviewer-2", "new_password": "another-strong-password",
            "is_active": "on", "_save": "저장",
        })
        self.assertEqual(response.status_code, 302)
        account = AppReviewAccount.objects.get(username="reviewer-2")
        self.assertTrue(check_password("another-strong-password", account.password_hash))
        self.assertNotEqual(account.password_hash, "another-strong-password")
        self.assertEqual(account.user.username, "reviewer-2")
        self.assertFalse(account.user.is_staff)
        self.assertFalse(account.user.is_superuser)
        response = self.client.get("/admin/core/appreviewaccount/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "앱 심사용 계정")
        self.assertNotContains(response, account.password_hash)

