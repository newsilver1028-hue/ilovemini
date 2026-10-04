from datetime import timedelta
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIRequestFactory
from .models import SeasonBanner
from .season_views import SeasonBannerView

class SeasonBannerTests(TestCase):
    def setUp(self):
        SeasonBanner.objects.all().delete()

    def response(self):
        return SeasonBannerView.as_view()(APIRequestFactory().get('/api/app/season-banner/'))

    def test_no_campaign_does_not_block_launch(self):
        self.assertEqual(self.response().data, {"banner": None})

    def test_only_current_active_campaign_and_priority(self):
        now = timezone.now()
        SeasonBanner.objects.create(title='미래', is_active=True, starts_at=now + timedelta(days=1), priority=1)
        SeasonBanner.objects.create(title='종료', is_active=True, ends_at=now - timedelta(minutes=1), priority=1)
        SeasonBanner.objects.create(title='비활성', priority=1)
        SeasonBanner.objects.create(title='일반', is_active=True, priority=20)
        chosen = SeasonBanner.objects.create(title='가을 이벤트', is_active=True, priority=2, image_url='https://example.com/autumn.png')
        response = self.response()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['banner']['id'], chosen.pk)
        self.assertEqual(response['Cache-Control'], 'no-store')

    def test_end_date_and_image_validation(self):
        now = timezone.now()
        with self.assertRaises(ValidationError):
            SeasonBanner(title='잘못된 날짜', starts_at=now, ends_at=now).full_clean()
        with self.assertRaises(ValidationError):
            SeasonBanner(title='잘못된 이미지', image_url='http://example.com/test.png').full_clean()
        with self.assertRaises(ValidationError):
            SeasonBanner(title='긴 표시', duration_seconds=20).full_clean()

    def test_public_api_limits_unsafe_data(self):
        SeasonBanner.objects.create(title='직접 입력', is_active=True, duration_seconds=99, image_url='http://example.com/unsafe.png')
        banner = self.response().data['banner']
        self.assertEqual(banner['duration_seconds'], 5)
        self.assertEqual(banner['image_url'], '')
