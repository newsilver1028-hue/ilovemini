import os
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from .models import Partner


class PatchLifecycleTests(TestCase):
    def test_bootstrap_redeploy_preserves_existing_password(self):
        User = get_user_model()
        user = User.objects.create_superuser(username='patch-admin', password='old-test-password-K8!')
        with patch.dict(os.environ, {'DJANGO_SUPERUSER_USERNAME': 'patch-admin', 'DJANGO_SUPERUSER_PASSWORD': 'new-test-password-J9!'}):
            call_command('bootstrap_superuser')
        user.refresh_from_db()
        self.assertTrue(user.check_password('old-test-password-K8!'))
        self.assertFalse(user.check_password('new-test-password-J9!'))

    def test_sync_preserves_shop_identity_and_separates_branches(self):
        old = Partner.objects.create(name='아이모터스랩', cafe_url='https://m.cafe.naver.com/ca-fe/cafes/13071593/menus/347')
        old_id = old.pk
        call_command('sync_ilovemini_partners')
        self.assertEqual(Partner.objects.get(name='아이모터스랩 성수점').pk, old_id)
        self.assertNotEqual(Partner.objects.get(name='아이모터스랩 죽전점').pk, old_id)
        self.assertEqual(Partner.objects.get(name='랩스타모터스').service_categories, ['정비'])
        call_command('sync_ilovemini_partners')
        self.assertEqual(Partner.objects.count(), 29)
