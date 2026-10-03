from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import NaverIdentity, PartnerStaff
from .naver_auth import user_for_profile
from .member_display import member_label

User = get_user_model()
class MemberDisplayTests(TestCase):
    def setUp(self):
        self.root = User.objects.create_superuser('displayadmin', 'admin@example.com', 'test-secret-9238')
        self.member = user_for_profile({'id':'display-member', 'nickname':'테스트회원', 'email':'member@example.com'})
        self.client.force_login(self.root)

    def test_profile_updates_existing_account_without_relinking(self):
        changed = user_for_profile({'id':'display-member', 'nickname':'새닉네임', 'email':'new@example.com'})
        self.assertEqual(changed.pk, self.member.pk)
        self.assertEqual(changed.email, 'new@example.com')
        self.assertIn('새닉네임', member_label(changed))
        user_for_profile({'id':'display-member'})
        changed.refresh_from_db()
        self.assertEqual(changed.email, 'new@example.com')

    def test_list_search_by_nickname_and_number(self):
        url = reverse('admin:auth_user_changelist')
        for query in ['테스트회원', str(self.member.pk), 'member@example.com']:
            response = self.client.get(url, {'q':query})
            self.assertContains(response, '테스트회원')

    def test_autocomplete_label_and_permissions(self):
        url = reverse('admin:core_partnerstaff_member_autocomplete')
        params = {'app_label':'core', 'model_name':'partnerstaff', 'field_name':'user', 'term':'테스트회원'}
        result = self.client.get(url, params)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()['results'][0]['text'], member_label(self.member))
        self.client.force_login(self.member)
        self.assertNotEqual(self.client.get(url, params).status_code, 200)

    def test_selected_account_readable(self):
        response = self.client.get(reverse('admin:core_partnerstaff_add'))
        self.assertEqual(response.status_code, 200)
        field = response.context['adminform'].form.fields['user']
        self.assertEqual(field.label_from_instance(self.member), member_label(self.member))
