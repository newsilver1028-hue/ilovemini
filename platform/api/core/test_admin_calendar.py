from django.contrib import admin
from django.contrib.admin.widgets import AdminDateWidget, AdminSplitDateTime
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.db import models
from django.test import RequestFactory, SimpleTestCase, TestCase
from django.urls import reverse


class AdminCalendarTests(SimpleTestCase):
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

    def test_dashboard_shows_policy_page_links(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "/privacy/")
        self.assertContains(response, "/terms/")
