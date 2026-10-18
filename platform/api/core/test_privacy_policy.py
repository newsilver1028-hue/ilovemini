from django.test import SimpleTestCase
from django.urls import reverse


class PrivacyPolicyPageTests(SimpleTestCase):
    def test_public_root_redirects_to_privacy_policy(self):
        response = self.client.get("/")
        self.assertRedirects(response, "/privacy/")

    def test_privacy_policy_page_is_public_and_contains_controller_contact(self):
        response = self.client.get(reverse("privacy_policy"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "개인정보 처리방침")
        self.assertContains(response, "커뮤니티명:</strong> 아이러브미니")
        self.assertContains(response, "개인정보 보호업무 담당 및 권리 요청:</strong> 아이러브미니")
        self.assertContains(response, "0507-1416-5035")
        self.assertNotContains(response, "운영자")
        self.assertContains(response, "사업자명:</strong> um(유엠)")
        self.assertContains(response, "um(유엠)")
        self.assertContains(response, "120-11-92135")
        self.assertContains(response, "0507-1416-5035")
        self.assertContains(response, "Render Services, Inc.")
        self.assertContains(response, "미국 오리건주")
        self.assertContains(response, "탈퇴일로부터 최대 1년")
        self.assertContains(response, "Hugging Face")
        self.assertContains(response, "OpenAI, L.L.C.")
        self.assertContains(response, "입력한 질문이 OpenAI API로 전송")
        self.assertNotContains(response, "초안입니다")
