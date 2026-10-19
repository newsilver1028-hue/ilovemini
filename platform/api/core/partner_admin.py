from django.contrib import admin
from django.contrib.admin import AdminSite
from django.db.models import Q
from django.db import transaction
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse
from django.urls import path, reverse
from django.utils.html import format_html_join

from .models import (
    LedgerEntry,
    LedgerEvidence,
    PartnerBooking,
    PartnerStaff,
)


def active_staff_for(request):
    if not request.user.is_authenticated:
        return PartnerStaff.objects.none()
    return PartnerStaff.objects.filter(
        user=request.user,
        is_active=True,
        partner__is_active=True,
    ).select_related("partner")


def staff_partners(request, *, booking=False, records=False):
    qs = active_staff_for(request)
    if booking:
        qs = qs.filter(can_manage_bookings=True)
    if records:
        qs = qs.filter(can_verify_records=True)
    return qs.values_list("partner_id", flat=True)


class PartnerAdminSite(AdminSite):
    site_header = "아이러브미니 협력업체 센터"
    site_title = "협력업체 센터"
    index_title = "업체 업무"
    login_template = "core/partner_admin_login.html"
    site_url = None

    def has_permission(self, request):
        return bool(
            request.user.is_authenticated
            and request.user.is_active
            and not request.user.is_superuser
            and active_staff_for(request).filter(
                Q(can_manage_bookings=True) | Q(can_verify_records=True)
            ).exists()
        )

    def get_app_list(self, request, app_label=None):
        app_list = super().get_app_list(request, app_label)
        names = {
            "PartnerBooking": "업체 예약",
            "LedgerEntry": "인증 정비기록",
        }
        for app in app_list:
            app["name"] = "업체 업무"
            for model in app["models"]:
                model["name"] = names.get(model["object_name"], model["name"])
        return app_list

    def get_urls(self):
        return [
            path(
                "ledger/<int:entry_id>/evidence/<int:evidence_id>/",
                self.admin_view(self.ledger_evidence_view),
                name="ledger-evidence",
            ),
        ] + super().get_urls()

    def ledger_evidence_view(self, request, entry_id, evidence_id):
        if not active_staff_for(request).filter(can_verify_records=True).exists():
            raise Http404
        partner_ids = staff_partners(request, records=True)
        evidence = LedgerEvidence.objects.select_related("entry").filter(
            pk=evidence_id,
            entry_id=entry_id,
            entry__source=LedgerEntry.Source.PARTNER,
            entry__partner_id__in=partner_ids,
        ).first()
        if not evidence:
            raise Http404
        response = HttpResponse(bytes(evidence.image_data), content_type=evidence.content_type)
        response["Cache-Control"] = "private, no-store"
        response["X-Content-Type-Options"] = "nosniff"
        return response


partner_admin_site = PartnerAdminSite(name="partner_admin")


@admin.register(PartnerBooking, site=partner_admin_site)
class PartnerBookingAdmin(admin.ModelAdmin):
    list_display = ("scheduled_at", "customer", "vehicle", "service_type", "status", "contact_phone")
    list_filter = ("status", "scheduled_at")
    search_fields = ("customer__username", "customer__naver_identity__nickname", "vehicle__model_name", "vehicle__plate_number", "service_type")
    list_select_related = ("customer", "vehicle", "partner")
    date_hierarchy = "scheduled_at"
    ordering = ("-requested_at",)
    actions = None
    fields = ("scheduled_at", "customer", "vehicle", "service_type", "customer_note", "contact_phone", "status", "partner_note")
    readonly_fields = ("scheduled_at", "customer", "vehicle", "service_type", "customer_note", "contact_phone")

    def get_queryset(self, request):
        return super().get_queryset(request).filter(
            partner_id__in=staff_partners(request, booking=True)
        ).select_related("partner", "customer", "vehicle")

    def has_module_permission(self, request):
        return active_staff_for(request).filter(can_manage_bookings=True).exists()

    def has_view_permission(self, request, obj=None):
        allowed = self.has_module_permission(request)
        return allowed and (obj is None or obj.partner_id in staff_partners(request, booking=True))

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        allowed = self.has_module_permission(request)
        if not allowed or (obj is not None and obj.partner_id not in staff_partners(request, booking=True)):
            return False
        return obj is None or obj.status in (PartnerBooking.Status.REQUESTED, PartnerBooking.Status.CONFIRMED)

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        if not change or obj.partner_id not in staff_partners(request, booking=True):
            raise Http404
        previous = PartnerBooking.objects.filter(pk=obj.pk, partner_id=obj.partner_id).values("status", "partner_note").first()
        if previous is None:
            raise Http404
        allowed = {
            PartnerBooking.Status.REQUESTED: {PartnerBooking.Status.CONFIRMED, PartnerBooking.Status.REJECTED},
            PartnerBooking.Status.CONFIRMED: {PartnerBooking.Status.COMPLETED},
        }
        if obj.status != previous["status"] and obj.status not in allowed.get(previous["status"], set()):
            raise PermissionDenied("현재 상태에서 선택할 수 없는 예약 변경입니다.")
        super().save_model(request, obj, form, change)
        if obj.status != previous["status"]:
            def notify_customer():
                try:
                    from .push import send_booking_status_notification
                    send_booking_status_notification(obj)
                except Exception:
                    import logging
                    logging.getLogger(__name__).exception("Partner admin booking notification failed (booking_id=%s)", obj.pk)
            transaction.on_commit(notify_customer)


@admin.register(LedgerEntry, site=partner_admin_site)
class PartnerLedgerEntryAdmin(admin.ModelAdmin):
    list_display = ("entry_date", "vehicle", "kind", "amount_krw", "odometer_km", "description", "evidence_count")
    list_filter = ("kind", "entry_date")
    search_fields = ("vehicle__model_name", "vehicle__plate_number", "description")
    list_select_related = ("partner", "vehicle")
    date_hierarchy = "entry_date"
    ordering = ("-entry_date", "-pk")
    actions = None

    def get_queryset(self, request):
        return super().get_queryset(request).filter(
            source=LedgerEntry.Source.PARTNER,
            partner_id__in=staff_partners(request, records=True),
        ).select_related("partner", "vehicle")

    def has_module_permission(self, request):
        return active_staff_for(request).filter(can_verify_records=True).exists()

    def has_view_permission(self, request, obj=None):
        allowed = self.has_module_permission(request)
        return allowed and (obj is None or obj.partner_id in staff_partners(request, records=True) and obj.source == LedgerEntry.Source.PARTNER)

    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False

    @admin.display(description="첨부 사진")
    def evidence_count(self, obj):
        images = obj.evidence_images.all()
        if not images:
            return "없음"
        url_name = f"{self.admin_site.name}:ledger-evidence"
        return format_html_join(
            " ", '<a href="{}" target="_blank" rel="noopener">사진 {}</a>',
            (
                (reverse(url_name, kwargs={"entry_id": obj.pk, "evidence_id": image.pk}), index)
                for index, image in enumerate(images, start=1)
            ),
        )
