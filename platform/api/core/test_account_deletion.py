from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from .models import (
    AppleIdentity,
    LedgerEntry,
    NaverIdentity,
    Partner,
    Vehicle,
    VehicleOwnership,
    LedgerEvidence,
)
from .apple_auth import AppleAuthorizationUnavailable
from .integrity import ledger_record_hash


class AccountDeletionTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            "member-to-delete", email="member@example.com", first_name="회원",
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_deletion_removes_login_and_unverified_vehicle_but_keeps_anonymized_certified_history(self):
        NaverIdentity.objects.create(
            user=self.user, subject="naver-account-subject", nickname="회원 별명",
        )
        ordinary_vehicle = Vehicle.objects.create(
            model_name="MINI Cooper", plate_number="12가3456", vin_hash="a" * 64,
        )
        VehicleOwnership.objects.create(user=self.user, vehicle=ordinary_vehicle)

        certified_vehicle = Vehicle.objects.create(
            model_name="MINI Cooper S", nickname="내 차", plate_number="34나7890",
            vin_hash="b" * 64,
        )
        VehicleOwnership.objects.create(user=self.user, vehicle=certified_vehicle)
        partner = Partner.objects.create(name="테스트 정비소")
        certified_entry = LedgerEntry.objects.create(
            vehicle=certified_vehicle,
            partner=partner,
            source=LedgerEntry.Source.PARTNER,
            kind=LedgerEntry.Kind.SERVICE,
            description="엔진오일 교환",
            evidence_url="https://example.com/private-receipt.jpg",
            line_items=[{"description": "12가3456 연락처 01000000000", "amount_krw": 10000}],
        )
        LedgerEvidence.objects.create(entry=certified_entry, image_data=b"private-photo",
                                      content_type="image/jpeg", file_name="receipt.jpg")
        new_owner = get_user_model().objects.create_user("new-current-owner")
        transferred_vehicle = Vehicle.objects.create(
            model_name="MINI Cooper", plate_number="56다1234",
        )
        VehicleOwnership.objects.create(
            user=self.user,
            vehicle=transferred_vehicle,
            ended_at=timezone.now() - timedelta(days=1),
        )
        VehicleOwnership.objects.create(user=new_owner, vehicle=transferred_vehicle)

        response = self.client.delete("/api/me/account/")

        self.assertEqual(response.status_code, 204)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertEqual(self.user.email, "")
        self.assertEqual(self.user.first_name, "")
        self.assertFalse(self.user.has_usable_password())
        self.assertFalse(NaverIdentity.objects.filter(user=self.user).exists())
        self.assertFalse(AppleIdentity.objects.filter(user=self.user).exists())
        self.assertFalse(Vehicle.objects.filter(pk=ordinary_vehicle.pk).exists())
        certified_vehicle.refresh_from_db()
        self.assertEqual(certified_vehicle.plate_number, "")
        self.assertEqual(certified_vehicle.vin_hash, "")
        self.assertEqual(certified_vehicle.nickname, "")
        self.assertGreaterEqual(
            certified_vehicle.retention_expires_at,
            timezone.now() + timedelta(days=364),
        )
        self.assertTrue(LedgerEntry.objects.filter(pk=certified_entry.pk).exists())
        certified_entry.refresh_from_db()
        self.assertEqual(certified_entry.evidence_url, "")
        self.assertEqual(certified_entry.line_items, [])
        self.assertEqual(certified_entry.record_hash, ledger_record_hash(certified_entry))
        self.assertFalse(LedgerEvidence.objects.filter(entry=certified_entry).exists())
        transferred_vehicle.refresh_from_db()
        self.assertEqual(transferred_vehicle.plate_number, "56다1234")
        self.assertEqual(transferred_vehicle.owner, new_owner)
        self.assertFalse(VehicleOwnership.objects.filter(
            vehicle=certified_vehicle, user=self.user, ended_at__isnull=True,
        ).exists())

    def test_requires_authentication(self):
        self.client.force_authenticate(None)
        response = self.client.delete("/api/me/account/")
        self.assertEqual(response.status_code, 401)

    def test_expired_certified_history_is_purged_by_retention_command(self):
        vehicle = Vehicle.objects.create(
            model_name="MINI Cooper S", retention_expires_at=timezone.now() - timedelta(days=1),
        )
        partner = Partner.objects.create(name="보관기간 만료 테스트 업체")
        entry = LedgerEntry.objects.create(
            vehicle=vehicle,
            partner=partner,
            source=LedgerEntry.Source.PARTNER,
            kind=LedgerEntry.Kind.SERVICE,
            description="보관기간 만료 기록",
        )

        call_command("purge_expired_member_history")

        self.assertFalse(Vehicle.objects.filter(pk=vehicle.pk).exists())
        self.assertFalse(LedgerEntry.objects.filter(pk=entry.pk).exists())

    def test_cleanup_does_not_delete_a_vehicle_with_a_current_owner(self):
        vehicle = Vehicle.objects.create(model_name="MINI", retention_expires_at=timezone.now() - timedelta(days=1))
        VehicleOwnership.objects.create(user=self.user, vehicle=vehicle)
        call_command("purge_expired_member_history")
        self.assertTrue(Vehicle.objects.filter(pk=vehicle.pk).exists())

    @patch("core.auth_views.apple_revocation_configured", return_value=False)
    def test_apple_without_server_key_is_not_reported_as_deleted(self, _configured):
        AppleIdentity.objects.create(user=self.user, subject="apple-subject")
        info = self.client.get("/api/me/account/")
        self.assertTrue(info.data["requires_apple_reauthentication"])
        self.assertFalse(info.data["deletion_available"])
        self.assertEqual(self.client.delete("/api/me/account/").status_code, 503)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        self.assertTrue(AppleIdentity.objects.filter(user=self.user).exists())

    @patch("core.auth_views.apple_revocation_configured", return_value=True)
    @patch("core.auth_views.verify_apple_identity", return_value={"sub": "different-member"})
    @patch("core.auth_views.revoke_apple_authorization")
    def test_wrong_apple_account_cannot_delete_member(self, revoke, _verify, _configured):
        AppleIdentity.objects.create(user=self.user, subject="apple-subject")
        result = self.client.delete("/api/me/account/", {
            "apple_identity_token": "id-token", "apple_nonce": "n" * 32,
            "apple_authorization_code": "one-time-code",
        }, format="json")
        self.assertEqual(result.status_code, 403)
        revoke.assert_not_called()
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

    @patch("core.auth_views.apple_revocation_configured", return_value=True)
    @patch("core.auth_views.verify_apple_identity", return_value={"sub": "apple-subject"})
    @patch("core.auth_views.revoke_apple_authorization")
    def test_apple_revocation_must_succeed_before_data_is_deleted(self, revoke, _verify, _configured):
        AppleIdentity.objects.create(user=self.user, subject="apple-subject")
        payload = {"apple_identity_token": "id-token", "apple_nonce": "n" * 32,
                   "apple_authorization_code": "one-time-code"}
        revoke.side_effect = AppleAuthorizationUnavailable
        self.assertEqual(self.client.delete("/api/me/account/", payload, format="json").status_code, 503)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        self.assertTrue(AppleIdentity.objects.filter(user=self.user).exists())
        revoke.side_effect = None
        self.assertEqual(self.client.delete("/api/me/account/", payload, format="json").status_code, 204)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertFalse(AppleIdentity.objects.filter(user=self.user).exists())
