from django.contrib import admin
from django.contrib.admin import AdminSite
from django import forms
from django.db.models import F, Q, Sum
from django.db import transaction
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import path, reverse
from django.utils.html import format_html_join
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.conf import settings
from datetime import datetime, time, timedelta

from .models import (
    LedgerEntry,
    LedgerEvidence,
    Partner,
    PartnerBooking,
    PartnerServiceDuration,
    PartnerWeeklySchedule,
    PartnerScheduleException,
    PartnerScheduleBlock,
    PartnerStaff,
    PartnerWorkOrder,
    PartnerPart,
    PartnerFinancialEntry,
    PartnerPurchaseLine,
    ServiceEstimate,
)
from .member_display import member_nickname


def active_staff_for(request):
    if not request.user.is_authenticated:
        return PartnerStaff.objects.none()
    return PartnerStaff.objects.filter(
        user=request.user,
        is_active=True,
        partner__is_active=True,
    ).select_related("partner")


def is_system_admin(request):
    user = request.user
    return bool(user.is_authenticated and user.is_active and user.is_staff and user.is_superuser)


def staff_partners(request, *, booking=False, records=False):
    if is_system_admin(request):
        return Partner.objects.filter(is_active=True).values_list("id", flat=True)
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
    index_template = "core/partner_admin_index.html"
    login_template = "core/partner_admin_login.html"
    site_url = None

    def each_context(self, request):
        context = super().each_context(request)
        context["is_partner_admin"] = True
        context["partner_application_options"] = Partner.objects.filter(is_active=True).order_by("name", "branch_label")
        context["partner_web_push_public_key"] = (
            getattr(settings, "WEB_PUSH_VAPID_PUBLIC_KEY", "") if self.has_permission(request) else ""
        )
        return context

    def has_permission(self, request):
        return bool(
            request.user.is_authenticated
            and request.user.is_active
            and (
                is_system_admin(request)
                or active_staff_for(request).filter(
                    Q(can_manage_bookings=True) | Q(can_verify_records=True)
                ).exists()
            )
        )

    def get_app_list(self, request, app_label=None):
        app_list = super().get_app_list(request, app_label)
        names = {
            "PartnerBooking": "업체 예약",
            "PartnerServiceDuration": "정비 항목별 작업 시간",
            "PartnerWeeklySchedule": "주간 예약 운영시간",
            "PartnerScheduleException": "날짜별 일정 변경·휴무",
            "PartnerScheduleBlock": "임시 예약 차단",
            "PartnerWorkOrder": "정비 접수·작업지시",
            "PartnerCustomer": "고객 대장",
            "PartnerVehicle": "업체 차량 대장",
            "PartnerPosIntegration": "POS 연동 설정",
            "PartnerPayment": "POS 결제 내역",
            "PartnerTaxInvoice": "전자세금계산서 발행 준비",
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
                "work-orders/<int:work_order_id>/quote/",
                self.admin_view(self.print_work_order_document),
                {"document_type": "quote"},
                name="partner-workorder-quote",
            ),
            path(
                "work-orders/<int:work_order_id>/<str:document_type>/",
                self.admin_view(self.print_work_order_document),
                name="partner-workorder-document",
            ),
            path(
                "estimates/<int:estimate_id>/print/",
                self.admin_view(self.print_service_estimate),
                name="partner-estimate-print",
            ),
            path(
                "exports/bookings.xlsx",
                self.admin_view(self.export_bookings),
                name="partner-booking-export",
            ),
            path(
                "exports/maintenance-records.xlsx",
                self.admin_view(self.export_maintenance_records),
                name="partner-maintenance-export",
            ),
            path("reports/", self.admin_view(self.operations_report), name="partner-operations-report"),
            path(
                "ledger/<int:entry_id>/evidence/<int:evidence_id>/",
                self.admin_view(self.ledger_evidence_view),
                name="ledger-evidence",
            ),
        ] + super().get_urls()

    @method_decorator(never_cache)
    def index(self, request, extra_context=None):
        context = self.each_context(request)
        context.update(extra_context or {})
        context["title"] = self.index_title
        context["app_list"] = self.get_app_list(request)

        can_manage_work = is_system_admin(request) or active_staff_for(request).filter(can_manage_bookings=True).exists()
        can_verify_records = is_system_admin(request) or active_staff_for(request).filter(can_verify_records=True).exists()
        partner_ids = staff_partners(request, booking=True)
        bookings = PartnerBooking.objects.filter(partner_id__in=partner_ids)
        orders = PartnerWorkOrder.objects.filter(partner_id__in=partner_ids).select_related("partner", "booking", "vehicle")
        today = timezone.localdate()
        active_statuses = [
            PartnerWorkOrder.Status.RECEIVED,
            PartnerWorkOrder.Status.INSPECTING,
            PartnerWorkOrder.Status.QUOTE,
            PartnerWorkOrder.Status.WAITING_APPROVAL,
            PartnerWorkOrder.Status.WAITING_PARTS,
            PartnerWorkOrder.Status.IN_PROGRESS,
            PartnerWorkOrder.Status.READY,
        ]
        context["partner_dashboard"] = {
            "can_manage_work": can_manage_work,
            "can_verify_records": can_verify_records,
            "today_bookings": bookings.filter(scheduled_at__date=today).count(),
            "booking_requests": bookings.filter(status=PartnerBooking.Status.REQUESTED).count(),
            "active_orders": orders.filter(status__in=active_statuses).count(),
            "awaiting_approval": orders.filter(status=PartnerWorkOrder.Status.WAITING_APPROVAL).count(),
            "low_stock_parts": PartnerPart.objects.filter(partner_id__in=partner_ids, is_active=True, stock_quantity__lte=F("reorder_level")).count(),
            "month_income": PartnerFinancialEntry.objects.filter(partner_id__in=partner_ids, kind=PartnerFinancialEntry.Kind.INCOME, occurred_at__year=today.year, occurred_at__month=today.month).aggregate(total=Sum("amount_krw"))["total"] or 0,
            "month_expense": PartnerFinancialEntry.objects.filter(partner_id__in=partner_ids, kind=PartnerFinancialEntry.Kind.EXPENSE, occurred_at__year=today.year, occurred_at__month=today.month).aggregate(total=Sum("amount_krw"))["total"] or 0,
            "recent_orders": orders.order_by("-updated_at", "-pk")[:8],
            "today": today,
        }
        # Surface urgent work in one tenant-scoped queue so staff can act without
        # searching across separate booking and repair lists.
        now = timezone.now()
        queue = []
        queue_specs = (
            (PartnerWorkOrder.Status.WAITING_APPROVAL, 0, "고객 승인 대기", "견적 확인·안내"),
            (PartnerWorkOrder.Status.READY, 1, "출고 대기", "수납·차량 인도 확인"),
            (PartnerWorkOrder.Status.WAITING_PARTS, 3, "부품 대기", "입고 일정 확인"),
            (PartnerWorkOrder.Status.RECEIVED, 4, "접수 미처리", "점검 시작"),
        )
        for status, priority, title, instruction in queue_specs:
            for row in orders.filter(status=status).order_by("updated_at", "pk")[:8]:
                queue.append({
                    "priority": priority, "sort_at": row.updated_at, "title": title,
                    "instruction": instruction,
                    "primary": row.plate_number or row.vehicle_model or row.customer_name or "차량 미입력",
                    "secondary": f"{row.customer_name or '고객 미입력'} · {row.updated_at:%m-%d %H:%M} 변경",
                    "url": reverse("partner_admin:core_partnerworkorder_change", args=[row.pk]),
                    "status": row.status,
                })
        stale_bookings = bookings.filter(
            status=PartnerBooking.Status.REQUESTED,
            requested_at__lt=now - timedelta(hours=24),
        ).select_related("vehicle").order_by("requested_at")[:8]
        for booking in stale_bookings:
            queue.append({
                "priority": 2, "sort_at": booking.requested_at,
                "title": "예약 요청 24시간 초과",
                "instruction": "고객에게 예약 가능 여부 회신",
                "primary": booking.vehicle.model_name if booking.vehicle else booking.service_type,
                "secondary": f"{member_nickname(booking.customer)} · {booking.requested_at:%m-%d %H:%M} 요청",
                "url": reverse("partner_admin:core_partnerbooking_change