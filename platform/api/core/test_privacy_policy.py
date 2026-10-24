from django.test import SimpleTestCase
from django.urls import reverse


class PrivacyPolicyPageTests(SimpleTestCase):
    def test_privacy_policy_page_is_public_and_contains_controller_contact(self):
        response = self.client.get(reverse("privacy_policy"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "개인정보 처리방침")
        self.assertNotContains(response, "커뮤니티명:")
        self.assertContains(response, "개인정보 보호업무 담당 및 권리 요청: 아이러브미니 개인정보 담당자")
        self.assertContains(response, "0507-1416-5035")
        self.assertNotContains(response, "운영자")
        self.assertContains(response, "사업자명 유엠(um) · 사업자등록번호 120-11-92135")
        self.assertContains(response, "유엠(um)")
        self.assertContains(response, "120-11-92135")
        self.assertContains(response, "0507-1416-5035")
        self.assertContains(response, "Render Services, Inc.")
        self.assertContains(response, "미국 오리건주")
        self.assertContains(response, "탈퇴일로부터 최대 1년")
        self.assertContains(response, "Hugging Face")
        self.assertNotContains(response, "OpenAI")
        self.assertNotContains(response, "AI 카페 검색")
        self.assertContains(response, "Apple 로그인")
        self.assertNotContains(response, "초안입니다")

    def test_terms_page_is_public_and_links_privacy_policy(self):
        response = self.client.get(reverse("terms_of_service"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "이용약관")
        self.assertContains(response, "/privacy/")
        self.assertContains(response, "아이러브미니 카페 회칙과 커뮤니티 이용")
        self.assertContains(response, "https://cafe.naver.com/minilover/book5082490")
        self.assertContains(response, "총칙, 회원, 동호회 구성")
        self.assertContains(response, "https://form.naver.com/response/Rh9L8MykI-6rrFIG1Ptbdw")
        self.assertContains(response, "네이버 카페의 신고 기능")
        self.assertContains(response, "차단 기능")
        self.assertContains(response, "게시물 주소, 작성자 닉네임")
        self.assertNotContains(response, "BMW")
