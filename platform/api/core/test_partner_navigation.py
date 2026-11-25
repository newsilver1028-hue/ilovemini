from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse
from core.models import Partner, PartnerStaff
from core.partner_admin import partner_admin_site


class PartnerNavigationTests(TestCase):
    def setUp(self):
        self.worker = get_user_model().objects.create_user("qa-navigation")
        self.partner = Partner.objects.create(name="검수용 업체", is_active=True)
        PartnerStaff.objects.create(user=self.worker, partner=self.partner, is_active=True, can_manage_bookings=True, can_verify_records=True)
        self.client.force_login(self.worker)

    def test_app_index_uses_partner_dashboard(self):
        response = self.client.get(reverse("partner_admin:app_list", args=["core"]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="workshop-title"')
        self.assertNotContains(response, "/admin/core/pointtransaction/")
        self.assertContains(response, "업체 관리자")

    def test_all_available_model_list_and_add_pages_render(self):
        request = RequestFactory().get("/partner-admin/")
        request.user = self.worker
        urls = {model[key] for app in partner_admin_site.get_app_list(request) for model in app["models"] for key in ("admin_url", "add_url") if model.get(key)}
        self.assertGreater(len(urls), 35)
        for url in sorted(urls):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_quote_share_title_is_korean(self):
        response = self.client.get(reverse("partner_admin:core_partnerquoteshare_changelist"))
        self.assertContains(response, '<h1>견적 링크 관리</h1>', html=True)
        self.assertNotContains(response, "Partner quote shares")

    def test_unknown_app_is_not_exposed(self):
        response = self.client.get("/partner-admin/onclass_control/")
        self.assertEqual(response.status_code, 404)

    def test_share_management_keeps_partner_and_booking_permission_scope(self):
        from datetime import timedelta
        from django.utils import timezone
        from core.models import PartnerWorkOrder, PartnerQuoteShare
        own_order = PartnerWorkOrder.objects.create(partner=self.partner)
        other_partner = Partner.objects.create(name="다른 검수 업체", is_active=True)
        other_order = PartnerWorkOrder.objects.create(partner=other_partner)
        own = PartnerQuoteShare.objects.create(work_order=own_order, expires_at=timezone.now()+timedelta(days=1))
        other = PartnerQuoteShare.objects.create(work_order=other_order, expires_at=timezone.now()+timedelta(days=1))
        response = self.client.get(reverse("partner_admin:core_partnerquoteshare_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["cl"].queryset), [own])
        response = self.client.get(reverse("partner_admin:core_partnerquoteshare_change", args=[other.pk]))
        self.assertIn(response.status_code, (302, 403, 404))
        self.assertNotContains(response, str(other.token), status_code=response.status_code)
        PartnerStaff.objects.filter(user=self.worker).update(can_manage_bookings=False)
        response = self.client.get(reverse("partner_admin:core_partnerquoteshare_changelist"))
        self.assertEqual(response.status_code, 403)
