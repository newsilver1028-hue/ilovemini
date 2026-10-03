from datetime import timedelta
from unittest.mock import patch
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from .models import NaverIdentity, NaverOAuthAttempt
from .naver_auth import digest, user_for_profile

PROFILE = dict(id='test-subject', name='테스트회원', email='test@example.com', nickname='테스트별명', profile_image='https://example.com/photo.png', gender='F', birthday='10-05', age='40-49', birthyear='1984', mobile='010-1234-5678')

class FullProfileTests(TestCase):
    def test_all_fields_and_existing_user_refresh(self):
        user = user_for_profile(PROFILE)
        identity = NaverIdentity.objects.get(user=user)
        for key, value in PROFILE.items():
            if key != 'id': self.assertEqual(getattr(identity, key), value)
        self.assertEqual(user.first_name, PROFILE['name'])
        self.assertEqual(user.email, PROFILE['email'])
        updated = dict(PROFILE, name='변경이름', mobile='010-9999-9999')
        self.assertEqual(user_for_profile(updated).pk, user.pk)
        identity.refresh_from_db()
        self.assertEqual(identity.name, '변경이름')
        self.assertEqual(identity.mobile, '010-9999-9999')

    def test_missing_fields_do_not_erase(self):
        user = user_for_profile(PROFILE)
        user_for_profile({'id': PROFILE['id'], 'nickname': '새별명'})
        identity = NaverIdentity.objects.get(user=user)
        self.assertEqual(identity.email, PROFILE['email'])
        self.assertEqual(identity.mobile, PROFILE['mobile'])

    def test_callback_complete_preserves_all_fields_and_clears_ticket_data(self):
        from .auth_views import NaverCallbackView, NaverCompleteView
        from rest_framework.test import APIRequestFactory
        factory = APIRequestFactory()
        attempt = NaverOAuthAttempt.objects.create(state_digest=digest('state'), expires_at=timezone.now()+timedelta(minutes=10))
        with patch('core.auth_views.exchange_code', return_value='token'), patch('core.auth_views.get_profile', return_value=PROFILE):
            response = NaverCallbackView.as_view()(factory.get('/', {'state':'state', 'code':'code'}))
        from urllib.parse import urlparse, parse_qs
        ticket = parse_qs(urlparse(response['Location']).query)['ticket'][0]
        attempt.refresh_from_db()
        self.assertEqual(attempt.profile_data['email'], PROFILE['email'])
        response = NaverCompleteView.as_view()(factory.post('/', {'ticket':ticket, 'terms_accepted':True, 'privacy_accepted':True}, format='json'))
        self.assertEqual(response.status_code, 200)
        identity = NaverIdentity.objects.get(subject=PROFILE['id'])
        for key,value in PROFILE.items():
            if key != 'id': self.assertEqual(getattr(identity,key), value)
        attempt.refresh_from_db()
        self.assertEqual(attempt.profile_data, {})
        self.assertIsNone(attempt.ticket_digest)
        response = NaverCompleteView.as_view()(factory.post('/', {'ticket':ticket, 'terms_accepted':True, 'privacy_accepted':True}, format='json'))
        self.assertEqual(response.status_code,400)
