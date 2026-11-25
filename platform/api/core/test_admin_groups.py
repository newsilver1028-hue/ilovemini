from django.test import SimpleTestCase
from core.templatetags.admin_groups import admin_groups


class AdminGroupTests(SimpleTestCase):
    def test_other_service_is_separate_and_permission_filtered(self):
        device = {"object_name": "Device", "name": "등록 기기"}
        estimate = {"object_name": "ServiceEstimate", "name": "정비 견적"}
        groups = admin_groups([{"models": [device, estimate]}])
        self.assertEqual([g["title"] for g in groups], ["연결 서비스 · 수업쉼표", "기타 관리"])
        self.assertEqual(groups[0]["models"], [device])
        self.assertEqual(groups[1]["models"], [estimate])
        self.assertEqual(sum(len(g["models"]) for g in groups), 2)

    def test_no_inaccessible_models_or_empty_groups_are_added(self):
        self.assertEqual(admin_groups([]), [])
        booking = {"object_name": "PartnerBooking", "name": "업체 예약"}
        groups = admin_groups([{"models": [booking]}])
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["models"], [booking])
