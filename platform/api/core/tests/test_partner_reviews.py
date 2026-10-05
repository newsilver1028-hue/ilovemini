from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import Partner, PartnerReview


class PartnerReviewApiTests(TestCase):
    def setUp(self):
        self.partner = Partner.objects.create(name="아이모터스랩", branch_label="성수점", is_active=True)
        self.client = APIClient()

    def test_public_can_read_reviews_and_partner_profile(self):
        response = self.client.get(f"/api/partners/{self.partner.pk}/reviews/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])
        profile = self.client.get(f"/api/partners/{self.partner.pk}/")
        self.assertEqual(profile.status_code, 200)
        self.assertEqual(profile.json()["branch_label"], "성수점")

    def test_review_requires_login_and_one_review_per_member(self):
        url = f"/api/partners/{self.partner.pk}/reviews/"
        self.assertEqual(self.client.post(url, {"rating": 5, "comment": "좋아요"}, format="json").status_code, 401)
        member = get_user_model().objects.create_user(username="partner-reviewer")
        self.client.force_authenticate(member)
        first = self.client.post(url, {"rating": 5, "comment": "좋아요"}, format="json")
        second = self.client.post(url, {"rating": 4, "comment": "수정"}, format="json")
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(PartnerReview.objects.filter(partner=self.partner, user=member).count(), 1)
        self.assertEqual(PartnerReview.objects.get(partner=self.partner, user=member).rating, 4)

    def test_rating_must_be_between_one_and_five(self):
        member = get_user_model().objects.create_user(username="partner-reviewer-2")
        self.client.force_authenticate(member)
        response = self.client.post(f"/api/partners/{self.partner.pk}/reviews/", {"rating": 6}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_service_history_returns_aggregate_only(self):
        response = self.client.get(f"/api/partners/{self.partner.pk}/service-history/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"total": 0, "by_kind": []})
