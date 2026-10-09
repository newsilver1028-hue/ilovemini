from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import NaverIdentity, Partner, PartnerReview
from core.serializers import PartnerReviewSerializer


class MemberCafeNicknameTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="nickname-member")
        self.identity = NaverIdentity.objects.create(
            user=self.user, subject="nickname-subject", nickname="네이버 프로필명"
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_member_can_set_cafe_nickname_and_overview_returns_it(self):
        response = self.client.patch(
            "/api/me/overview/", {"cafe_nickname": "  카페 닉네임  "}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.identity.refresh_from_db()
        self.assertEqual(self.identity.cafe_nickname, "카페 닉네임")
        overview = self.client.get("/api/me/overview/")
        self.assertEqual(overview.status_code, 200)
        self.assertEqual(overview.json()["cafe_nickname"], "카페 닉네임")

    def test_cafe_nickname_is_used_for_partner_review_name(self):
        partner = Partner.objects.create(name="닉네임 테스트 업체", is_active=True)
        review = PartnerReview.objects.create(
            partner=partner, user=self.user, rating=5, comment="테스트"
        )
        self.identity.cafe_nickname = "카페 별명"
        self.identity.save(update_fields=["cafe_nickname"])
        self.assertEqual(PartnerReviewSerializer(review).data["reviewer_name"], "카페 별명")

    def test_cafe_nickname_is_required_and_limited_to_40_characters(self):
        empty = self.client.patch("/api/me/overview/", {"cafe_nickname": "  "}, format="json")
        too_long = self.client.patch(
            "/api/me/overview/", {"cafe_nickname": "가" * 41}, format="json"
        )
        self.assertEqual(empty.status_code, 400)
        self.assertEqual(too_long.status_code, 400)
