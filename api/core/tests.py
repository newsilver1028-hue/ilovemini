from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test import override_settings
from django.core.management import call_command
from django.utils import timezone
from rest_framework.test import APIClient
from datetime import date, timedelta
from unittest.mock import patch
import json
from urllib.parse import unquote
from .admin import NoticeAdminForm, OfferAdminForm, PartnerAdminForm
from .models import LedgerEntry, Reminder, Vehicle, VehicleOwnership, Partner, PartnerStaff, Notice, PushDevice, AttendanceCheckin, PartnerBooking

User = get_user_model()


class CafeSearchTests(TestCase):
    def test_cafe_search_requires_server_credentials(self):
        response = APIClient().get("/api/cafe/search/?q=미션")
        self.assertEqual(response.status_code, 503)

    @override_settings(NAVER_API_HUB_CLIENT_ID="test-id", NAVER_API_HUB_CLIENT_SECRET="test-secret")
    def test_cafe_search_calls_naver_api_live_and_returns_links_without_persisting(self):
        class FakeResponse:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self): return json.dumps({"total": 1, "items": [{
                "title": "<b>MINI</b> 미션 정비", "description": "락업클러치 점검 내용",
                "link": "https://cafe.naver.com/ilovemini/123", "cafename": "아이러브미니",
                "cafeurl": "https://cafe.naver.com/ilovemini",
            }]}).encode()
        with patch("core.views.urlopen", return_value=FakeResponse()) as request:
            response = APIClient().get("/api/cafe/search/?q=미션")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["items"][0]["title"], "MINI 미션 정비")
        self.assertEqual(response.data["items"][0]["link"], "https://cafe.naver.com/ilovemini/123")
        self.assertIn("아이러브미니", unquote(request.call_args.args[0].full_url))

    def test_cafe_latest_requires_server_credentials(self):
        response = APIClient().get("/api/cafe/latest/")
        self.assertEqual(response.status_code, 503)

    @override_settings(NAVER_API_HUB_CLIENT_ID="test-id", NAVER_API_HUB_CLIENT_SECRET="test-secret")
    def test_cafe_latest_uses_date_sorted_naver_results_and_keeps_ten_cafe_articles(self):
        cache.clear()
        cafe_items = [{
            "title": f"<b>MINI</b> 최신글 {index}", "description": "회원 게시글 요약",
            "link": f"https://cafe.naver.com/minilover/{index}", "cafename": "아이러브미니",
            "cafeurl": "https://cafe.naver.com/minilover",
        } for index in range(12)]
        cafe_items.append({
            "title": "MINI 다른 카페 글", "description": "제외되어야 함",
            "link": "https://cafe.naver.com/another/999", "cafename": "다른 자동차 카페",
            "cafeurl": "https://cafe.naver.com/another",
        })

        class FakeResponse:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self): return json.dumps({"total": 1000, "lastBuildDate": "Thu, 1 Oct 2026 08:00:00 +0900", "items": cafe_items}).encode()

        with patch("core.views.urlopen", return_value=FakeResponse()) as upstream:
            response = APIClient().get("/api/cafe/latest/")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(len(response.data["items"]), 10)
        self.assertEqual(response.data["items"][0]["title"], "MINI 최신글 0")
        self.assertTrue(response.data["live_search"])
        self.assertEqual(response.data["source"], "NAVER API HUB · MINI 검색 최신순 · 아이러브미니 공개글")
        params = dict(part.split("=", 1) for part in unquote(upstream.call_args.args[0].full_url.split("?",1)[1]).split("&"))
        self.assertEqual(params["sort"], "date")
        self.assertEqual(params["query"], "MINI")
        self.assertEqual(params["display"], "100")

    def test_cafe_answer_requires_server_key(self):
        with override_settings(OPENAI_API_KEY=""):
            response = APIClient().post("/api/cafe/answer/", {"q": "F56 미션"}, format="json")
        self.assertEqual(response.status_code, 503)

    @override_settings(OPENAI_API_KEY="server-test-key", OPENAI_SEARCH_MODEL="gpt-test")
    def test_cafe_answer_searches_public_cafe_and_returns_only_cafe_citations(self):
        class FakeResponse:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self): return json.dumps({
                "output_text": "카페 공개글에 따르면 우선 진단이 필요합니다.",
                "output": [{"type": "message", "content": [{"type": "output_text", "text": "카페 공개글에 따르면 우선 진단이 필요합니다.", "annotations": [
                    {"type": "url_citation", "url_citation": {"url": "https://cafe.naver.com/minilover/123", "title": "F56 미션 점검"}},
                    {"type": "url_citation", "url_citation": {"url": "https://example.com/untrusted", "title": "무관한 출처"}},
                ]}]}]
            }).encode()

        with patch("core.views.urlopen", return_value=FakeResponse()) as upstream:
            response = APIClient().post("/api/cafe/answer/", {"q": "F56 미션 변속 충격"}, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertTrue(response.data["live_search"])
        self.assertEqual(response.data["sources"], [{"title": "F56 미션 점검", "url": "https://cafe.naver.com/minilover/123"}])
        request = upstream.call_args.args[0]
        request_body = json.loads(request.data)
        self.assertEqual(request.get_header("Authorization"), "Bearer server-test-key")
        self.assertEqual(request_body["tools"][0]["filters"]["allowed_domains"], ["cafe.naver.com"])
        self.assertEqual(request_body["tool_choice"], "required")
        self.assertIn("site:cafe.naver.com/minilover", request_body["input"])


class AttendanceCheckinTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="attendance-member", password="Long-test-password-789")
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_daily_checkin_is_idempotent_and_awards_points_once(self):
        today = date(2026, 9, 27)
        with patch("core.views.timezone.localdate", return_value=today):
            first = self.client.post("/api/attendance/", {}, format="json")
            second = self.client.post("/api/attendance/", {}, format="json")
            summary = self.client.get("/api/attendance/")
        self.assertEqual(first.status_code, 201)
        self.assertEqual(first.data["earned_points"], 1000)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.data["earned_points"], 0)
        self.assertEqual(summary.data["balance_points"], 1000)
        self.assertEqual(AttendanceCheckin.objects.filter(user=self.user).count(), 1)

    def test_seventh_consecutive_checkin_awards_streak_bonus(self):
        start = date(2026, 9, 21)
        for offset in range(7):
            with patch("core.views.timezone.localdate", return_value=start + timedelta(days=offset)):
                response = self.client.post("/api/attendance/", {}, format="json")
        self.assertEqual(response.data["earned_points"], 4000)
        self.assertEqual(response.data["streak_days"], 7)
        self.assertEqual(response.data["balance_points"], 10000)

class ApiAccessTests(TestCase):
    def setUp(self):
        cache.clear()  # Isolate rate-limit counters between independent tests.
        self.member = User.objects.create_user(username="mini-owner", password="Long-test-password-123")
        self.other = User.objects.create_user(username="other-owner", password="Long-test-password-456")
        self.mine = self.create_owned_vehicle(self.member, model_name="MINI Cooper S", model_year=2021)
        self.theirs = self.create_owned_vehicle(self.other, model_name="MINI One", model_year=2018)
        self.client = APIClient()
        self.client.force_authenticate(self.member)

    def create_owned_vehicle(self, user, **fields):
        vehicle = Vehicle.objects.create(**fields)
        VehicleOwnership.objects.create(vehicle=vehicle, user=user, verification_method="test")
        return vehicle

    def test_vehicle_list_only_contains_signed_in_members_cars(self):
        response = self.client.get("/api/vehicles/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in response.data], [self.mine.id])

    def test_new_vehicle_creates_a_claimed_ownership_and_passport_id(self):
        response = self.client.post("/api/vehicles/", {
            "manufacturer": "MINI", "model_name": "MINI Cooper JCW", "generation": "F56",
            "model_year": 2021,
        }, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        vehicle = Vehicle.objects.get(pk=response.data["id"])
        ownership = vehicle.current_ownership
        self.assertEqual(ownership.user, self.member)
        self.assertEqual(ownership.verification_status, VehicleOwnership.VerificationStatus.USER_CLAIMED)
        self.assertEqual(str(vehicle.public_id), response.data["public_id"])

    def test_partner_booking_is_saved_and_visible_to_customer(self):
        partner = Partner.objects.create(name="예약 테스트 업체", is_active=True)
        scheduled_at = (timezone.now() + timedelta(days=2)).isoformat()
        response = self.client.post("/api/bookings/", {
            "partner": partner.pk, "vehicle": self.mine.pk, "scheduled_at": scheduled_at,
            "service_type": "엔진오일 교환", "contact_phone": "010-1234-5678", "customer_note": "오전 희망",
        }, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        booking = PartnerBooking.objects.get(pk=response.data["id"])
        self.assertEqual(booking.customer, self.member)
        self.assertEqual(booking.status, PartnerBooking.Status.REQUESTED)
        self.assertEqual(self.client.get("/api/bookings/").data[0]["partner_name"], partner.name)

    def test_booking_access_is_scoped_and_partner_can_only_respond_to_assigned_shop(self):
        shop = Partner.objects.create(name="권한 예약업체", is_active=True)
        other_shop = Partner.objects.create(name="다른 예약업체", is_active=True)
        booking = PartnerBooking.objects.create(customer=self.member, partner=shop,
            scheduled_at=timezone.now() + timedelta(days=1), service_type="정비")
        shop_user = User.objects.create_user(username="booking-shop", password="Long-test-password-789")
        other_user = User.objects.create_user(username="other-booking-shop", password="Long-test-password-789")
        PartnerStaff.objects.create(user=shop_user, partner=shop, can_manage_bookings=True, is_active=True)
        PartnerStaff.objects.create(user=other_user, partner=other_shop, can_manage_bookings=True, is_active=True)
        shop_client = APIClient(); shop_client.force_authenticate(shop_user)
        other_client = APIClient(); other_client.force_authenticate(other_user)
        self.assertEqual(shop_client.get("/api/bookings/").data[0]["id"], booking.pk)
        self.assertEqual(other_client.get("/api/bookings/").data, [])
        denied = other_client.post(f"/api/bookings/{booking.pk}/respond/", {"status": "confirmed"}, format="json")
        self.assertEqual(denied.status_code, 404)
        accepted = shop_client.post(f"/api/bookings/{booking.pk}/respond/", {"status": "confirmed"}, format="json")
        self.assertEqual(accepted.status_code, 200, accepted.data)
        self.assertEqual(booking.__class__.objects.get(pk=booking.pk).status, PartnerBooking.Status.CONFIRMED)
        cancelled = self.client.post(f"/api/bookings/{booking.pk}/cancel/", {}, format="json")
        self.assertEqual(cancelled.status_code, 200)
        self.assertEqual(booking.__class__.objects.get(pk=booking.pk).status, PartnerBooking.Status.CANCELLED)

    def test_passport_scan_requires_assigned_active_service_staff(self):
        public_data = {"vehicle_public_id": str(self.mine.public_id)}
        denied = self.client.post("/api/vehicles/scan-passport/", public_data, format="json")
        self.assertEqual(denied.status_code, 403)
        partner = Partner.objects.create(name="QR 업체", is_active=True)
        worker = User.objects.create_user(username="qr-worker", password="Long-test-password-789")
        PartnerStaff.objects.create(user=worker, partner=partner, can_verify_records=True, is_active=True)
        worker_client = APIClient(); worker_client.force_authenticate(worker)
        ok = worker_client.post("/api/vehicles/scan-passport/", public_data, format="json")
        self.assertEqual(ok.status_code, 200, ok.data)
        self.assertEqual(ok.data["vehicle"]["model_name"], self.mine.model_name)

    def test_member_cannot_create_ledger_entry_for_another_members_car(self):
        response = self.client.post("/api/ledger/", {
            "vehicle": self.theirs.id, "kind": "service", "amount_krw": 50000,
            "description": "정비",
        }, format="json")
        self.assertEqual(response.status_code, 400)

    def test_new_ledger_odometer_updates_vehicle_mileage(self):
        response = self.client.post("/api/ledger/", {
            "vehicle": self.mine.id, "kind": "service", "amount_krw": 50000,
            "description": "엔진오일", "odometer_km": 42000,
        }, format="json")
        self.assertEqual(response.status_code, 201)
        self.mine.refresh_from_db()
        self.assertEqual(self.mine.current_odometer_km, 42000)

    def test_reminder_list_can_be_filtered_by_vehicle(self):
        another_mini = self.create_owned_vehicle(self.member, model_name="MINI Cooper SE")
        mine_reminder = Reminder.objects.create(vehicle=self.mine, title="엔진오일")
        Reminder.objects.create(vehicle=another_mini, title="타이어 점검")
        response = self.client.get(f"/api/reminders/?vehicle={self.mine.pk}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([row["id"] for row in response.data], [mine_reminder.pk])

    def test_vehicle_transfer_moves_car_and_its_history_after_buyer_accepts(self):
        entry = LedgerEntry.objects.create(
            vehicle=self.mine, kind="service", amount_krw=80000, description="엔진오일 교환", odometer_km=41000,
        )
        reminder = Reminder.objects.create(vehicle=self.mine, title="다음 엔진오일 교환", notification_sent_at=timezone.now())
        issued = self.client.post(f"/api/vehicles/{self.mine.pk}/transfer-code/")
        self.assertEqual(issued.status_code, 201)
        code = issued.data["code"]

        buyer_client = APIClient()
        buyer_client.force_authenticate(self.other)
        preview = buyer_client.post("/api/vehicles/preview-transfer/", {"code": code}, format="json")
        self.assertEqual(preview.status_code, 200)
        self.assertEqual(preview.data["model_name"], self.mine.model_name)
        self.assertEqual(preview.data["ledger_count"], 1)
        self.assertEqual(preview.data["verified_record_count"], 0)
        self.assertEqual(preview.data["correction_count"], 0)
        self.assertEqual(preview.data["reminder_count"], 1)

        accepted = buyer_client.post("/api/vehicles/accept-transfer/", {"code": code}, format="json")
        self.assertEqual(accepted.status_code, 200)
        self.mine.refresh_from_db()
        self.assertEqual(self.mine.owner, self.other)
        ownerships = list(self.mine.ownerships.order_by("started_at"))
        self.assertEqual(len(ownerships), 2)
        self.assertEqual(ownerships[0].user, self.member)
        self.assertIsNotNone(ownerships[0].ended_at)
        self.assertEqual(ownerships[1].user, self.other)
        self.assertIsNone(ownerships[1].ended_at)
        self.assertTrue(LedgerEntry.objects.filter(pk=entry.pk, vehicle=self.mine).exists())
        self.assertTrue(Reminder.objects.filter(pk=reminder.pk, vehicle=self.mine).exists())
        reminder.refresh_from_db()
        self.assertIsNotNone(reminder.notification_sent_at)

        buyer_vehicles = buyer_client.get("/api/vehicles/")
        self.assertIn(self.mine.pk, [item["id"] for item in buyer_vehicles.data])
        seller_vehicles = self.client.get("/api/vehicles/")
        self.assertNotIn(self.mine.pk, [item["id"] for item in seller_vehicles.data])
        replay = buyer_client.post("/api/vehicles/accept-transfer/", {"code": code}, format="json")
        self.assertEqual(replay.status_code, 400)

    def test_vehicle_maintenance_summary_reports_verified_history_and_due_items(self):
        partner_user = User.objects.create_user(username="summary-shop", password="Long-test-password-789")
        partner = Partner.objects.create(name="요약 협력업체", is_active=True)
        PartnerStaff.objects.create(partner=partner, user=partner_user, can_verify_records=True, is_active=True)
        partner_client = APIClient()
        partner_client.force_authenticate(partner_user)
        service = partner_client.post("/api/ledger/partner-verified/", {
            "vehicle_public_id": str(self.mine.public_id), "partner": partner.pk, "kind": "service",
            "entry_date": timezone.localdate().isoformat(), "odometer_km": 43000,
            "description": "엔진오일 교환",
        }, format="json")
        self.assertEqual(service.status_code, 201, service.data)
        Reminder.objects.create(
            vehicle=self.mine,
            title="엔진오일 점검",
            due_date=timezone.localdate(),
            due_odometer_km=50000,
        )

        response = self.client.get(f"/api/vehicles/{self.mine.pk}/maintenance-summary/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["ledger_count"], 1)
        self.assertEqual(response.data["verified_record_count"], 1)
        self.assertEqual(response.data["pending_reminder_count"], 1)
        self.assertEqual(response.data["overdue_reminder_count"], 1)
        self.assertEqual(response.data["last_maintenance"]["description"], "엔진오일 교환")
        self.assertEqual(response.data["next_due_odometer_km"], 50000)

    def test_seller_can_cancel_pending_transfer_code(self):
        issued = self.client.post(f"/api/vehicles/{self.mine.pk}/transfer-code/")
        self.assertEqual(issued.status_code, 201)
        cancelled = self.client.post(f"/api/vehicles/{self.mine.pk}/cancel-transfer/")
        self.assertEqual(cancelled.status_code, 200)
        self.assertEqual(cancelled.data["cancelled"], 1)

        buyer_client = APIClient()
        buyer_client.force_authenticate(self.other)
        response = buyer_client.post("/api/vehicles/accept-transfer/", {"code": issued.data["code"]}, format="json")
        self.assertEqual(response.status_code, 400)
        self.mine.refresh_from_db()
        self.assertEqual(self.mine.owner, self.member)

    def test_authorized_partner_creates_immutable_verified_service_record(self):
        partner_user = User.objects.create_user(username="verified-shop", password="Long-test-password-789")
        partner = Partner.objects.create(name="인증 협력업체", is_active=True)
        PartnerStaff.objects.create(partner=partner, user=partner_user, can_verify_records=True, is_active=True)
        partner_client = APIClient()
        partner_client.force_authenticate(partner_user)
        created = partner_client.post("/api/ledger/partner-verified/", {
            "vehicle_public_id": str(self.mine.public_id),
            "partner": partner.pk,
            "kind": "service",
            "entry_date": "2026-09-25",
            "odometer_km": 43000,
            "amount_krw": 250000,
            "description": "엔진마운트 교환",
            "part_number": "MINI-MOUNT-001",
            "evidence_url": "https://example.com/evidence/receipt-1",
        }, format="json")
        self.assertEqual(created.status_code, 201, created.data)
        self.assertEqual(created.data["source"], "partner")
        self.assertEqual(created.data["trust_label"], "업체 인증")
        self.assertTrue(created.data["integrity_valid"])

        entry = LedgerEntry.objects.get(pk=created.data["id"])
        self.assertTrue(entry.record_hash)
        self.assertEqual(entry.partner, partner)
        self.assertEqual(entry.verified_by, partner_user)
        LedgerEntry.objects.filter(pk=entry.pk).update(description="임의 변경")
        tampered = self.client.get(f"/api/ledger/{entry.pk}/")
        self.assertEqual(tampered.status_code, 200)
        self.assertFalse(tampered.data["integrity_valid"])
        self.assertEqual(tampered.data["trust_label"], "검증 이상")
        replay = partner_client.post("/api/ledger/partner-verified/", {
            "vehicle_public_id": str(self.mine.public_id), "partner": partner.pk, "kind": "service",
            "odometer_km": 43000, "description": "중복",
        }, format="json")
        self.assertEqual(replay.status_code, 201, replay.data)
        blocked_delete = self.client.delete(f"/api/ledger/{entry.pk}/")
        self.assertEqual(blocked_delete.status_code, 409)
        blocked_vehicle_delete = self.client.delete(f"/api/vehicles/{self.mine.pk}/")
        self.assertEqual(blocked_vehicle_delete.status_code, 409)

    def test_partner_cannot_accidentally_duplicate_same_vehicle_service(self):
        partner_user = User.objects.create_user(username="duplicate-shop", password="Long-test-password-789")
        partner = Partner.objects.create(name="중복 방지 업체", is_active=True)
        PartnerStaff.objects.create(partner=partner, user=partner_user, can_verify_records=True, is_active=True)
        partner_client = APIClient(); partner_client.force_authenticate(partner_user)
        payload = {"vehicle_public_id": str(self.mine.public_id), "partner": partner.pk,
                   "kind": "service", "entry_date": timezone.localdate().isoformat(),
                   "odometer_km": 43000, "description": "엔진오일 교환"}
        first = partner_client.post("/api/ledger/partner-verified/", payload, format="json")
        duplicate = partner_client.post("/api/ledger/partner-verified/", payload, format="json")
        self.assertEqual(first.status_code, 201, first.data)
        self.assertEqual(duplicate.status_code, 409)
        self.assertEqual(duplicate.data["duplicate_record_id"], first.data["id"])

    def test_verified_record_integrity_binds_its_source(self):
        partner_user = User.objects.create_user(username="source-shop", password="Long-test-password-789")
        partner = Partner.objects.create(name="출처 검증 업체", is_active=True)
        PartnerStaff.objects.create(partner=partner, user=partner_user, can_verify_records=True, is_active=True)
        partner_client = APIClient()
        partner_client.force_authenticate(partner_user)
        created = partner_client.post("/api/ledger/partner-verified/", {
            "vehicle_public_id": str(self.mine.public_id), "partner": partner.pk, "kind": "service",
            "odometer_km": 43000, "description": "타이어 교체",
        }, format="json")
        self.assertEqual(created.status_code, 201, created.data)
        LedgerEntry.objects.filter(pk=created.data["id"]).update(source=LedgerEntry.Source.OWNER)
        response = self.client.get(f"/api/ledger/{created.data['id']}/")
        self.assertFalse(response.data["integrity_valid"])

    def test_verified_record_rejects_non_https_evidence(self):
        partner_user = User.objects.create_user(username="evidence-shop", password="Long-test-password-789")
        partner = Partner.objects.create(name="증빙 검증 업체", is_active=True)
        PartnerStaff.objects.create(partner=partner, user=partner_user, can_verify_records=True, is_active=True)
        partner_client = APIClient()
        partner_client.force_authenticate(partner_user)
        response = partner_client.post("/api/ledger/partner-verified/", {
            "vehicle_public_id": str(self.mine.public_id), "partner": partner.pk, "kind": "service",
            "odometer_km": 43000, "description": "미션오일 교환", "evidence_url": "http://example.com/receipt",
        }, format="json")
        self.assertEqual(response.status_code, 400)

    def test_partner_correction_appends_record_and_keeps_original_unchanged(self):
        partner_user = User.objects.create_user(username="correction-shop", password="Long-test-password-789")
        partner = Partner.objects.create(name="정정 업체", is_active=True)
        PartnerStaff.objects.create(partner=partner, user=partner_user, can_verify_records=True, is_active=True)
        partner_client = APIClient()
        partner_client.force_authenticate(partner_user)

        original_response = partner_client.post("/api/ledger/partner-verified/", {
            "vehicle_public_id": str(self.mine.public_id), "partner": partner.pk, "kind": "service",
            "odometer_km": 43000, "description": "엔진오일 교환", "amount_krw": 120000,
        }, format="json")
        self.assertEqual(original_response.status_code, 201, original_response.data)
        original = LedgerEntry.objects.get(pk=original_response.data["id"])

        correction_response = partner_client.post("/api/ledger/partner-verified/", {
            "vehicle_public_id": str(self.mine.public_id), "partner": partner.pk, "kind": "service",
            "odometer_km": 43000, "description": "엔진오일 및 필터 교환", "amount_krw": 120000,
            "corrects": original.pk, "correction_reason": "필터 작업 내역 누락 정정",
        }, format="json")
        self.assertEqual(correction_response.status_code, 201, correction_response.data)
        original.refresh_from_db()
        self.assertEqual(original.description, "엔진오일 교환")
        self.assertTrue(original.corrections.filter(pk=correction_response.data["id"]).exists())
        self.assertTrue(correction_response.data["integrity_valid"])
        self.assertEqual(correction_response.data["corrects"], original.pk)
        history = self.client.get(f"/api/ledger/?vehicle={self.mine.pk}")
        original_row = next(row for row in history.data if row["id"] == original.pk)
        self.assertTrue(original_row["is_corrected"])

    def test_partner_correction_requires_reason_and_same_shop(self):
        partner_user = User.objects.create_user(username="correction-guard", password="Long-test-password-789")
        partner = Partner.objects.create(name="원 업체", is_active=True)
        other_partner = Partner.objects.create(name="다른 업체", is_active=True)
        PartnerStaff.objects.create(partner=partner, user=partner_user, can_verify_records=True, is_active=True)
        PartnerStaff.objects.create(partner=other_partner, user=partner_user, can_verify_records=True, is_active=True)
        partner_client = APIClient()
        partner_client.force_authenticate(partner_user)
        original = partner_client.post("/api/ledger/partner-verified/", {
            "vehicle_public_id": str(self.mine.public_id), "partner": partner.pk, "kind": "service",
            "odometer_km": 43000, "description": "타이어 교체",
        }, format="json")
        self.assertEqual(original.status_code, 201, original.data)

        no_reason = partner_client.post("/api/ledger/partner-verified/", {
            "vehicle_public_id": str(self.mine.public_id), "partner": partner.pk, "kind": "service",
            "odometer_km": 43000, "description": "정정 시도", "corrects": original.data["id"],
        }, format="json")
        self.assertEqual(no_reason.status_code, 400)

        wrong_shop = partner_client.post("/api/ledger/partner-verified/", {
            "vehicle_public_id": str(self.mine.public_id), "partner": other_partner.pk, "kind": "service",
            "odometer_km": 43000, "description": "다른 업체 정정", "corrects": original.data["id"],
            "correction_reason": "업체 불일치 시험",
        }, format="json")
        self.assertEqual(wrong_shop.status_code, 400)

    def test_unapproved_partner_user_cannot_create_verified_record(self):
        partner_user = User.objects.create_user(username="unapproved-shop", password="Long-test-password-999")
        partner = Partner.objects.create(name="권한 없는 업체", is_active=True)
        partner_client = APIClient()
        partner_client.force_authenticate(partner_user)
        response = partner_client.post("/api/ledger/partner-verified/", {
            "vehicle_public_id": str(self.mine.public_id), "partner": partner.pk, "kind": "service",
            "odometer_km": 43000, "description": "무권한 기록",
        }, format="json")
        self.assertEqual(response.status_code, 403)

    def test_only_active_partners_are_public(self):
        Partner.objects.create(name="확인된 업체", is_active=True)
        Partner.objects.create(name="비공개 업체", is_active=False)
        self.client.force_authenticate(user=None)
        response = self.client.get("/api/partners/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["name"] for item in response.data], ["확인된 업체"])

    def test_unpublished_notice_is_not_public(self):
        Notice.objects.create(title="초안", is_published=False)
        self.client.force_authenticate(user=None)
        response = self.client.get("/api/notices/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

    def test_push_token_is_registered_to_signed_in_member(self):
        response = self.client.post("/api/push/devices/", {"installation_id": "firebase-installation-id", "platform": "ios"}, format="json")
        self.assertEqual(response.status_code, 200)
        device = PushDevice.objects.get(installation_id="firebase-installation-id")
        self.assertEqual(device.user, self.member)
        self.assertEqual(device.platform, PushDevice.Platform.IOS)

    def test_member_cannot_unregister_another_members_push_token(self):
        device = PushDevice.objects.create(user=self.other, installation_id="other-installation-id", platform=PushDevice.Platform.ANDROID)
        response = self.client.delete("/api/push/devices/", {"installation_id": device.installation_id}, format="json")
        self.assertEqual(response.status_code, 204)
        self.assertTrue(PushDevice.objects.filter(pk=device.pk, user=self.other).exists())

from urllib.parse import parse_qs, urlparse
from django.test import override_settings
from unittest.mock import patch
from .models import NaverIdentity, MemberConsent
from rest_framework.test import APIClient

class NaverLoginTests(TestCase):
    def setUp(self):
        self.client = APIClient()
    @override_settings(ALLOWED_HOSTS=["testserver"], NAVER_CLIENT_ID="test-client", NAVER_CLIENT_SECRET="test-secret", NAVER_REDIRECT_URI="https://api.example.test/api/auth/naver/callback/")
    def test_first_naver_login_creates_member_and_one_time_app_ticket(self):
        start = self.client.post("/api/auth/naver/start/")
        self.assertEqual(start.status_code, 200)
        auth_url = urlparse(start.data["authorization_url"])
        state = parse_qs(auth_url.query)["state"][0]
        with patch("core.auth_views.exchange_code", return_value="provider-token"), patch(
            "core.auth_views.get_profile", return_value={"id": "naver-subject-1", "nickname": "미니오너"}
        ):
            callback = self.client.get("/api/auth/naver/callback/", {"state": state, "code": "oauth-code"})
        self.assertEqual(callback.status_code, 302, getattr(callback, "data", callback.content))
        ticket = parse_qs(urlparse(callback["Location"]).query)["ticket"][0]
        self.assertEqual(NaverIdentity.objects.count(), 0)
        declined = self.client.post("/api/auth/naver/complete/", {"ticket": ticket}, format="json")
        self.assertEqual(declined.status_code, 400)
        completed = self.client.post("/api/auth/naver/complete/", {"ticket": ticket, "terms_accepted": True, "privacy_accepted": True}, format="json")
        self.assertEqual(completed.status_code, 200)
        self.assertIn("access", completed.data)
        self.assertEqual(NaverIdentity.objects.count(), 1)
        self.assertEqual(MemberConsent.objects.count(), 1)
        self.assertTrue(MemberConsent.objects.get().terms_accepted_at)
        replay = self.client.post("/api/auth/naver/complete/", {"ticket": ticket, "terms_accepted": True, "privacy_accepted": True}, format="json")
        self.assertEqual(replay.status_code, 400)

    @override_settings(ALLOWED_HOSTS=["testserver"], NAVER_CLIENT_ID="test-client", NAVER_CLIENT_SECRET="test-secret", NAVER_REDIRECT_URI="https://api.example.test/api/auth/naver/callback/")
    def test_unknown_oauth_state_is_rejected(self):
        response = self.client.get("/api/auth/naver/callback/", {"state": "not-a-real-state", "code": "x"})
        self.assertEqual(response.status_code, 400)

    @override_settings(NAVER_CLIENT_ID="", NAVER_REDIRECT_URI="")
    def test_login_start_requires_provider_configuration(self):
        response = self.client.post("/api/auth/naver/start/")
        self.assertEqual(response.status_code, 503)


class AdminContentFormTests(TestCase):
    def test_partner_categories_are_entered_as_comma_separated_text(self):
        form = PartnerAdminForm(data={
            "name": "테스트 MINI 업체",
            "display_order": 0,
            "service_categories": "정비, 튜닝, 정비, ",
            "is_active": True,
            "is_sponsored": False,
        })
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["service_categories"], ["정비", "튜닝"])

    def test_notice_expiry_must_follow_publication_time(self):
        form = NoticeAdminForm(data={
            "title": "테스트 공지",
            "summary": "",
            "body": "",
            "category": "notice",
            "original_url": "",
            "published_at": "2026-10-02 10:00:00",
            "expires_at": "2026-10-01 10:00:00",
            "is_published": True,
            "is_pinned": False,
        })
        self.assertFalse(form.is_valid())
        self.assertIn("expires_at", form.errors)

    def test_offer_end_must_follow_start(self):
        partner = Partner.objects.create(name="테스트 제휴 업체")
        form = OfferAdminForm(data={
            "partner": partner.pk,
            "title": "테스트 혜택",
            "description": "",
            "starts_at": "2026-10-02 10:00:00",
            "ends_at": "2026-10-01 10:00:00",
            "redemption_instructions": "",
            "is_active": True,
        })
        self.assertFalse(form.is_valid())
        self.assertIn("ends_at", form.errors)


class PartnerSyncCommandTests(TestCase):
    def test_sync_creates_and_updates_the_exact_operator_list_idempotently(self):
        Partner.objects.create(name="랩스터터스")
        call_command("sync_ilovemini_partners", verbosity=0)
        self.assertEqual(Partner.objects.count(), 28)
        self.assertEqual(Partner.objects.filter(name__startswith="아이모터스랩").count(), 2)
        self.assertEqual(Partner.objects.get(name="군팩토리").region, "서울 양천구 목동")
        self.assertEqual(Partner.objects.get(name="카카오파츠 서초").service_categories, ["전장", "오디오·전장"])
        partner = Partner.objects.get(name="랩스타모터스")
        self.assertTrue(partner.is_active)
        self.assertEqual(partner.cafe_url, "https://m.cafe.naver.com/ca-fe/cafes/13071593/menus/286")
        self.assertFalse(Partner.objects.filter(name="랩스터터스").exists())
        package = Partner.objects.get(name="대한민국대표 금호타이어")
        self.assertEqual(package.service_categories, ["신차패키지", "타이어"])
        self.assertEqual(package.cafe_url, "")
        pending = Partner.objects.filter(region="지역 확인 필요", cafe_url="")
        self.assertEqual(pending.count(), 3)
        self.assertEqual(set(pending.values_list("name", flat=True)), {
            "렌트리스 얼마면탈까", "수입차부품 프린트랩", "대한민국대표 금호타이어",
        })

        call_command("sync_ilovemini_partners", verbosity=0)
        self.assertEqual(Partner.objects.count(), 28)


class HandoverPrivacyTests(TestCase):
    def setUp(self):
        cache.clear()
        self.seller = User.objects.create_user(username="privacy-seller")
        self.buyer = User.objects.create_user(username="privacy-buyer")
        self.vehicle = Vehicle.objects.create(model_name="MINI Cooper S", model_year=2022,
                                              nickname="개인 별명", passport_public=True)
        VehicleOwnership.objects.create(vehicle=self.vehicle, user=self.seller)
        self.entry = LedgerEntry.objects.create(
            vehicle=self.vehicle, kind="service", amount_krw=123000, odometer_km=45600,
            description="이전 차주 전화 010-1234-5678", part_number="개인 메모",
            evidence_url="https://example.com/private-receipt")
        self.reminder = Reminder.objects.create(vehicle=self.vehicle, title="집 주소에서 픽업",
                                               due_date=timezone.localdate())
        self.client = APIClient()
        self.client.force_authenticate(self.seller)
        issued = self.client.post(f"/api/vehicles/{self.vehicle.pk}/transfer-code/")
        self.assertEqual(issued.status_code, 201, issued.data)
        self.client.force_authenticate(self.buyer)
        accepted = self.client.post("/api/vehicles/accept-transfer/", {"code": issued.data["code"]}, format="json")
        self.assertEqual(accepted.status_code, 200, accepted.data)

    def test_inherited_history_exposes_structured_facts_without_private_details(self):
        summary = self.client.get(f"/api/vehicles/{self.vehicle.pk}/maintenance-summary/").data
        rows = [self.client.get("/api/ledger/").data[0],
                self.client.get(f"/api/ledger/{self.entry.pk}/").data,
                summary["last_maintenance"]]
        for row in rows:
            self.assertTrue(row["details_redacted"])
            self.assertEqual(row["description"], self.entry.get_kind_display())
            self.assertEqual(row["evidence_url"], "")
            self.assertEqual(row["part_number"], "")
            self.assertIsNone(row["amount_krw"])
            self.assertEqual(row["odometer_km"], 45600)
        self.assertEqual(summary["pending_reminder_count"], 0)
        self.entry.refresh_from_db()
        self.assertIn("010-1234-5678", self.entry.description)
        self.vehicle.refresh_from_db()
        self.assertEqual(self.vehicle.nickname, "")
        self.assertFalse(self.vehicle.passport_public)

    def test_buyer_cannot_change_old_records_or_receive_private_reminders(self):
        from .push import send_reminder_notification
        url = f"/api/ledger/{self.entry.pk}/"
        self.assertEqual(self.client.patch(url, {"description": "변경"}, format="json").status_code, 409)
        self.assertEqual(self.client.delete(url).status_code, 409)
        self.assertEqual(self.client.get("/api/reminders/").data, [])
        self.assertEqual(self.client.get(f"/api/reminders/{self.reminder.pk}/").status_code, 404)
        self.assertEqual(send_reminder_notification(self.reminder, "date"), 0)
        new = self.client.post("/api/ledger/", {
            "vehicle": self.vehicle.pk, "kind": "service", "amount_krw": 10000,
            "description": "새 차주 기록"}, format="json")
        self.assertEqual(new.status_code, 201, new.data)
        self.assertFalse(new.data["details_redacted"])
        self.assertEqual(new.data["description"], "새 차주 기록")


class RefreshTokenTests(TestCase):
    def test_refresh_issues_working_access_token_and_rejects_invalid_token(self):
        from rest_framework_simplejwt.tokens import RefreshToken
        user = User.objects.create_user(username="refresh-user")
        client = APIClient()
        response = client.post("/api/auth/token/refresh/", {"refresh": str(RefreshToken.for_user(user))}, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
        self.assertEqual(client.get("/api/vehicles/").status_code, 200)
        invalid = client.post("/api/auth/token/refresh/", {"refresh": "invalid"}, format="json")
        self.assertEqual(invalid.status_code, 401)
