from django.contrib import admin
from django.contrib.admin.widgets import AdminDateWidget, AdminSplitDateTime
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.conf import settings
from django.db import models
from django.test import RequestFactory, TestCase
from django.urls import reverse
from .models import LedgerEntry, Partner, PartnerBooking, PointRedemptionRequest, PointTransaction, Vehicle


class AdminCalendarTests(TestCase):
    def test_editable_date_fields_in_registered_admins_have_calendar_widgets(self):
        request = RequestFactory().get("/admin/")
        request.user = AnonymousUser()
        checked_fields = 0

        for model, model_admin in admin.site._registry.items():
            form = model_admin.get_form(request)()
            for model_field in model._meta.fields:
                if model_field.name not in form.fields:
                    continue
                widget = form.fields[model_field.name].widget
                if isinstance(model_field, models.DateField):
                    self.assertEqual(
                        model_admin.change_list_template,
                        "admin/core/change_list_with_calendar.html",
                        model.__name__,
                    )
                if isinstance(model_field, models.DateTimeField):
                    self.assertIsInstance(widget, AdminSplitDateTime, f"{model.__name__}.{model_field.name}")
                    checked_fields += 1
                elif isinstance(model_field, models.DateField):
                    self.assertIsInstance(widget, AdminDateWidget, f"{model.__name__}.{model_field.name}")
                    checked_fields += 1

        self.assertGreater(checked_fields, 0)

    def test_policy_pages_are_linkable_from_admin_navigation(self):
        self.assertEqual(reverse("privacy_policy"), "/privacy/")
        self.assertEqual(reverse("terms_of_service"), "/terms/")


class AdminCalendarPageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.admin_user = User.objects.create_superuser(
            username="admin-calendar-test", email="calendar@example.com", password="test-password-123"
        )

    def assert_single_mini_calendar(self, response):
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.count(b'admin-mini-calendar"'), 1)
        self.assertNotContains(response, 'id="date-hierarchy"')

    def test_model_changelist_renders_one_mini_calendar(self):
        self.client.force_login(self.admin_user)
        ledger_response = self.client.get(reverse("admin:core_ledgerentry_changelist"))
        self.assert_single_mini_calendar(ledger_response)

        vehicle_response = self.client.get(reverse("admin:core_vehicle_changelist"))
        self.assert_single_mini_calendar(vehicle_response)

    def test_central_partner_booking_menu_is_available_and_calendarized(self):
        self.client.force_login(self.admin_user)
        dashboard = self.client.get(reverse("admin:index"))
        self.assertContains(dashboard, reverse("admin:core_partnerbooking_changelist"))

        response = self.client.get(reverse("admin:core_partnerbooking_changelist"))
        self.assert_single_mini_calendar(response)
        model_admin = admin.site._registry[PartnerBooking]
        request = RequestFactory().get("/admin/")
        request.user = self.admin_user
        self.assertFalse(model_admin.has_add_permission(request))
        self.assertFalse(model_admin.has_delete_permission(request))

    def test_cancelled_booking_reason_is_visible_in_admin_and_calendar_count(self):
        from django.contrib.auth import get_user_model
        from django.utils import timezone
        from datetime import timedelta
        customer = get_user_model().objects.create_user(username="booking-customer")
        partner = Partner.objects.create(name="취소 확인 업체", is_active=True)
        scheduled_at = timezone.now()
        selected_day = timezone.localtime(scheduled_at).date()
        vehicle = Vehicle.objects.create(model_name="MINI 쿠퍼")
        PartnerBooking.objects.create(
            customer=customer,
            partner=partner,
            vehicle=vehicle,
            scheduled_at=scheduled_at,
            service_type="엔진오일 교환",
            status=PartnerBooking.Status.CANCELLED,
            cancellation_reason="회원 사정으로 일정 취소",
        )
        LedgerEntry.objects.create(
            vehicle=vehicle,
            partner=partner,
            source=LedgerEntry.Source.PARTNER,
            kind=LedgerEntry.Kind.SERVICE,
            entry_date=selected_day,
            amount_krw=120000,
            description="엔진오일 교환",
        )
        PointTransaction.objects.create(
            user=customer, partner=partner,
            transaction_type=PointTransaction.Type.SERVICE_EARN,
            points_delta=1200, memo="정비 결제 적립",
        )
        PointTransaction.objects.create(
            user=customer, partner=partner,
            transaction_type=PointTransaction.Type.REDEMPTION,
            points_delta=-500, memo="업체 포인트 사용",
        )
        PointRedemptionRequest.objects.create(
            member=customer, partner=partner, payment_amount_krw=50000,
            points_requested=500, status=PointRedemptionRequest.Status.COMPLETED,
            completed_at=scheduled_at, expires_at=scheduled_at + timedelta(minutes=10),
        )
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("admin:core_partnerbooking_changelist"), {
            "scheduled_at__year": selected_day.year,
            "scheduled_at__month": selected_day.month,
            "scheduled_at__day": selected_day.day,
        })

        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context.get("booking_day_report"), response.wsgi_request.GET)
        self.assertContains(response, "회원 사정으로 일정 취소")
        self.assertContains(response, "취소 1건")
        self.assertContains(response, "인증 정비 등록액 120,000원")
        self.assertContains(response, "포인트 적립 1,200P")
        self.assertContains(response, "포인트 사용 500P")
        self.assertContains(response, "포인트 결제 1건 · 총 50,000원")
        self.assertContains(response, "포인트 사용 후 결제액 49,500원")
        self.assertContains(response, "엔진오일 교환")
        self.assertContains(response, "업체 포인트 사용")

    def test_read_only_model_lists_use_clean_titles(self):
        self.client.force_login(self.admin_user)
        for route in (
            "admin:core_vehicleownership_changelist",
            "admin:core_attendancecheckin_changelist",
            "admin:core_pointtransaction_changelist",
            "admin:core_pointredemptionrequest_changelist",
            "admin:core_recordcorrectionrequest_changelist",
        ):
            with self.subTest(route=route):
                response = self.client.get(reverse(route))
                self.assertEqual(response.status_code, 200)
                clean_title = response.context["cl"].opts.verbose_name_plural
                self.assertEqual(response.context["title"], clean_title)
                self.assertEqual(response.context["cl"].title, clean_title)
                self.assertNotIn("보기위한", response.context["title"])
                self.assertContains(response, f"<title>{clean_title} · ILOVEMINI 관리자</title>")

    def test_dashboard_shows_policy_page_links(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "/privacy/")
        self.assertContains(response, "/terms/")

    def test_admin_custom_domain_routes_to_partner_login(self):
        response = self.client.get("/", HTTP_HOST="admin.ilovemini.co.kr")
        self.assertRedirects(response, "/partner-admin/login/", fetch_redirect_response=False)

        shortcut = self.client.get("/partner/", HTTP_HOST="admin.ilovemini.co.kr")
        self.assertRedirects(shortcut, "/partner-admin/login/", fetch_redirect_response=False)

        self.assertIn("admin.ilovemini.co.kr", settings.ALLOWED_HOSTS)
        self.assertIn("https://admin.ilovemini.co.kr", settings.CSRF_TRUSTED_ORIGINS)
