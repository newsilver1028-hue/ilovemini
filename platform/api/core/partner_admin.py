from django.contrib import admin
from django.contrib.admin import AdminSite
from django.db.models import Q
from django.db import transaction
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse
from django.urls import path, reverse
from django.utils.html import format_html_join
from django.utils import timezone
from django.conf import settings
from datetime import datetime, time, timedelta

from .models import (
    LedgerEntry,
    LedgerEvidence,
    PartnerBooking,
    PartnerStaff,
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

    def each_context(self, request):
        context = super().each_context(request)
        context["is_partner_admin"] = True
        context["partner_web_push_public_key"] = (
            getattr(settings, "WEB_PUSH_VAPID_PUBLIC_KEY", "") if self.has_permission(request) else ""
        )
        return context

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
                "exports/bookings.xlsx",
                self.admin_view(self.export_bookings),
                name="partner-booking-export",
            ),
            path(
                "exports/maintenance-records.xlsx",
                self.admin_view(self.export_maintenance_records),
                name="partner-maintenance-export",
            ),
            path(
                "ledger/<int:entry_id>/evidence/<int:evidence_id>/",
                self.admin_view(self.ledger_evidence_view),
                name="ledger-evidence",
            ),
        ] + super().get_urls()

    @staticmethod
    def _excel_response(filename, title, headers, rows):
        from io import BytesIO
        from openpyxl import Workbook
        from openpyxl.styles import Alignment, Font, PatternFill
        from openpyxl.utils import get_column_letter

        workbook = Workbook()
        sheet = workbook.active
        sheet.title = title[:31]
        sheet.append(headers)
        for row in rows:
            safe_row = []
            for value in row:
                if isinstance(value, str) and value[:1] in ("=", "+", "-", "@", "\t"):
                    value = "'" + value
                safe_row.append(value)
            sheet.append(safe_row)
        sheet.freeze_panes = "A2"
        sheet.auto_filter.ref = sheet.dimensions
        for cell in sheet[1]:
            cell.font = Font(name="맑은 고딕", bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="B3213B")
            cell.alignment = Alignment(vertical="center")
        sheet.row_dimensions[1].height = 26
        for column in sheet.columns:
            values = [len(str(cell.value or "")) for cell in column]
            width = min(max(max(values, default=8) + 2, 12), 42)
            sheet.column_dimensions[get_column_letter(column[0].column)].width = width
            for cell in column[1:]:
                cell.alignment = Alignment(vertical="top", wrap_text=True)
        output = BytesIO()
        workbook.save(output)
        response = HttpResponse(
            output.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        response["Cache-Control"] = "private, no-store"
        return response

    def export_bookings(self, request):
        staff = active_staff_for(request).filter(can_manage_bookings=True)
        if not staff.exists():
            raise Http404
        partner_ids = staff.values_list("partner_id", flat=True)
        bookings = PartnerBooking.objects.filter(partner_id__in=partner_ids).select_related(
            "partner", "customer__naver_identity", "customer__apple_identity", "vehicle"
        ).order_by("-scheduled_at", "-pk")
        rows = []
        for booking in bookings.iterator():
            vehicle = booking.vehicle
            rows.append((
                timezone.localtime(booking.scheduled_at).strftime("%Y-%m-%d %H:%M"),
                vehicle.plate_number if vehicle else "",
                booking.contact_phone or "미등록",
                vehicle.model_name if vehicle else "차량 정보 없음",
                booking.partner.name,
                timezone.localtime(booking.requested_at).strftime("%Y-%m-%d %H:%M"),
                booking.service_type,
                booking.get_status_display(),
                booking.customer_note,
                booking.partner_note,
            ))
        return self._excel_response(
            f"ilovemini-bookings-{timezone.localdate():%Y%m%d}.xlsx",
            "예약 관리대장",
            ["예약 일시", "차량번호", "연락처", "차량", "업체", "요청 일시", "작업 종류", "예약 상태", "요청 사항", "업체 메모"],
            rows,
        )

    def export_maintenance_records(self, request):
        staff = active_staff_for(request).filter(can_verify_records=True)
        if not staff.exists():
            raise Http404
        partner_ids = staff.values_list("partner_id", flat=True)
        entries = LedgerEntry.objects.filter(
            source=LedgerEntry.Source.PARTNER,
            partner_id__in=partner_ids,
        ).select_related("partner", "vehicle", "verified_by__naver_identity", "verified_by__apple_identity").prefetch_related(
            "evidence_images"
        ).order_by("-entry_date", "-pk")
        rows = []
        for entry in entries.iterator(chunk_size=200):
            vehicle = entry.vehicle
            verified_by = entry.verified_by
            line_items = entry.line_items if isinstance(entry.line_items, list) else []
            item_values = []
            for item in line_items:
                if not isinstance(item, dict) or not str(item.get("name", "")).strip():
                    continue
                try:
                    amount = int(item.get("amount_krw") or 0)
                except (TypeError, ValueError):
                    amount = 0
                item_values.append(f"{str(item.get('name')).strip()}: {amount:,}원")
            rows.append((
                entry.entry_date.strftime("%Y-%m-%d"),
                timezone.localtime(entry.verified_at).strftime("%Y-%m-%d %H:%M") if entry.verified_at else "",
                entry.partner.name if entry.partner else "",
                vehicle.model_name if vehicle else "차량 정보 없음",
                vehicle.plate_number if vehicle else "",
                entry.odometer_km,
                entry.get_kind_display(),
                " / ".join(item_values),
                entry.amount_krw,
                entry.description,
                entry.evidence_images.count(),
                member_nickname(verified_by) if verified_by else "",
            ))
        return self._excel_response(
            f"ilovemini-maintenance-records-{timezone.localdate():%Y%m%d}.xlsx",
            "정비 관리대장",
            ["정비 일자", "등록 일시", "업체", "차량", "차량번호", "주행거리(km)", "작업 종류", "항목별 금액", "총액(원)", "정비 내용", "첨부 사진 수", "등록 담당자"],
            rows,
        )

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


class PartnerBookingStatusFilter(admin.SimpleListFilter):
    title = "예약 상태"
    parameter_name = "status"

    def lookups(self, request, model_admin):
        return PartnerBooking.Status.choices

    def queryset(self, request, queryset):
        return queryset.filter(status=self.value()) if self.value() else queryset


@admin.register(PartnerBooking, site=partner_admin_site)
class PartnerBookingAdmin(admin.ModelAdmin):
    change_list_template = "admin/core/partnerbooking/change_list.html"
    change_form_template = "admin/core/partnerbooking/change_form.html"
    list_display = ("booking_time", "vehicle_plate", "contact_phone_display", "vehicle_model", "service_label", "status_label")
    list_filter = (PartnerBookingStatusFilter,)
    search_fields = ("vehicle__model_name", "vehicle__plate_number", "contact_phone", "service_type")
    list_select_related = ("vehicle", "partner")
    date_hierarchy = None
    ordering = ("-requested_at",)
    actions = None
    fields = ("vehicle_registration", "contact_phone_display", "booking_time", "service_label", "customer_note_display", "status", "partner_note")
    readonly_fields = ("vehicle_registration", "contact_phone_display", "booking_time", "service_label", "customer_note_display")

    @admin.display(description="차량번호 / 차량")
    def vehicle_registration(self, obj):
        if not obj.vehicle:
            return "차량 정보 없음"
        plate = obj.vehicle.plate_number or "차량번호 미등록"
        return f"{plate} · {obj.vehicle.model_name}"

    @admin.display(description="예약 일시", ordering="scheduled_at")
    def booking_time(self, obj):
        return timezone.localtime(obj.scheduled_at).strftime("%Y-%m-%d %H:%M")

    @admin.display(description="차량번호", ordering="vehicle__plate_number")
    def vehicle_plate(self, obj):
        return obj.vehicle.plate_number if obj.vehicle and obj.vehicle.plate_number else "미등록"

    @admin.display(description="차량")
    def vehicle_model(self, obj):
        return obj.vehicle.model_name if obj.vehicle else "차량 정보 없음"

    @admin.display(description="연락처", ordering="contact_phone")
    def contact_phone_display(self, obj):
        return obj.contact_phone or "미등록"

    @admin.display(description="작업 종류", ordering="service_type")
    def service_label(self, obj):
        return obj.service_type or "미등록"

    @admin.display(description="예약 상태", ordering="status")
    def status_label(self, obj):
        return obj.get_status_display()

    @admin.display(description="요청 사항")
    def customer_note_display(self, obj):
        return obj.customer_note or "없음"

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        field = super().formfield_for_dbfield(db_field, request, **kwargs)
        labels = {"status": "예약 상태", "partner_note": "업체 메모"}
        if field and db_field.name in labels:
            field.label = labels[db_field.name]
        if field and db_field.name == "status":
            field.widget.attrs.update({"class": "partner-booking-status"})
        return field

    def get_queryset(self, request):
        return super().get_queryset(request).filter(
            partner_id__in=staff_partners(request, booking=True)
        ).select_related("partner", "customer", "vehicle")

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        today = timezone.localdate()
        year = request.GET.get("scheduled_at__year", "")
        month_number = request.GET.get("scheduled_at__month", "")
        try:
            month_start = datetime.strptime(f"{year}-{month_number}", "%Y-%m").date().replace(day=1)
        except ValueError:
            month_start = today.replace(day=1)
        next_month = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
        prev_month = (month_start - timedelta(days=1)).replace(day=1)
        grid_start = month_start - timedelta(days=month_start.weekday())
        final_day = next_month - timedelta(days=1)
        grid_end = final_day + timedelta(days=6 - final_day.weekday())
        bookings = self.get_queryset(request).filter(
            scheduled_at__gte=timezone.make_aware(datetime.combine(month_start, time.min)),
            scheduled_at__lt=timezone.make_aware(datetime.combine(next_month, time.min)),
        ).order_by("scheduled_at", "pk")
        events_by_day = {}
        for booking in bookings:
            vehicle = booking.vehicle
            event = {
                "time": timezone.localtime(booking.scheduled_at).strftime("%H:%M"),
                "plate": vehicle.plate_number if vehicle and vehicle.plate_number else "차량번호 미등록",
                "phone": booking.contact_phone or "연락처 미등록",
                "service": booking.service_type,
                "status": booking.get_status_display(),
                "status_code": booking.status,
                "change_url": reverse(f"{self.admin_site.name}:core_partnerbooking_change", args=[booking.pk]) if booking.status in (PartnerBooking.Status.REQUESTED, PartnerBooking.Status.CONFIRMED) else "",
            }
            events_by_day.setdefault(timezone.localtime(booking.scheduled_at).date(), []).append(event)
        weeks = []
        current_day = grid_start
        while current_day <= grid_end:
            week = []
            for _ in range(7):
                week.append({
                    "date": current_day,
                    "day": current_day.day,
                    "in_month": current_day.month == month_start.month,
                    "is_today": current_day == today,
                    "events": events_by_day.get(current_day, []),
                })
                current_day += timedelta(days=1)
            weeks.append(week)
        extra_context.update({
            "partner_calendar_month": month_start,
            "partner_calendar_prev": prev_month.strftime("%Y-%m"),
            "partner_calendar_next": next_month.strftime("%Y-%m"),
            "partner_calendar_weeks": weeks,
            "partner_calendar_weekdays": ["월", "화", "수", "목", "금", "토", "일"],
        })
        return super().changelist_view(request, extra_context=extra_context)

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
    change_list_template = "admin/core/ledgerentry/change_list.html"
    list_display = ("entry_date", "vehicle_plate", "vehicle_model", "kind_display", "amount_display", "odometer_display", "description_display", "evidence_count")
    list_filter = ("kind", "entry_date")
    search_fields = ("vehicle__model_name", "vehicle__plate_number", "description")
    list_select_related = ("partner", "vehicle")
    date_hierarchy = "entry_date"
    ordering = ("-entry_date", "-pk")
    actions = None

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context.setdefault("title", "인증 정비기록 조회")
        today = timezone.localdate()
        year = request.GET.get("entry_date__year", "")
        month_number = request.GET.get("entry_date__month", "")
        try:
            month_start = datetime.strptime(f"{year}-{month_number}", "%Y-%m").date().replace(day=1)
        except ValueError:
            month_start = today.replace(day=1)
        next_month = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
        prev_month = (month_start - timedelta(days=1)).replace(day=1)
        grid_start = month_start - timedelta(days=month_start.weekday())
        final_day = next_month - timedelta(days=1)
        grid_end = final_day + timedelta(days=6 - final_day.weekday())
        entries = self.get_queryset(request).filter(
            entry_date__gte=month_start, entry_date__lt=next_month
        ).order_by("entry_date", "pk")
        entries_by_day = {}
        for entry in entries:
            vehicle = entry.vehicle
            entries_by_day.setdefault(entry.entry_date, []).append({
                "plate": vehicle.plate_number if vehicle and vehicle.plate_number else "번호 미등록",
                "kind": entry.get_kind_display(),
                "amount": f"{entry.amount_krw:,}원",
            })
        weeks = []
        current_day = grid_start
        while current_day <= grid_end:
            week = []
            for _ in range(7):
                week.append({
                    "date": current_day,
                    "day": current_day.day,
                    "in_month": current_day.month == month_start.month,
                    "is_today": current_day == today,
                    "events": entries_by_day.get(current_day, []),
                })
                current_day += timedelta(days=1)
            weeks.append(week)
        extra_context.update({
            "partner_calendar_month": month_start,
            "partner_calendar_prev": prev_month.strftime("%Y-%m"),
            "partner_calendar_next": next_month.strftime("%Y-%m"),
            "partner_calendar_weeks": weeks,
            "partner_calendar_weekdays": ["월", "화", "수", "목", "금", "토", "일"],
        })
        return super().changelist_view(request, extra_context=extra_context)

    @admin.display(description="차량번호", ordering="vehicle__plate_number")
    def vehicle_plate(self, obj):
        return obj.vehicle.plate_number if obj.vehicle and obj.vehicle.plate_number else "미등록"

    @admin.display(description="차량", ordering="vehicle__model_name")
    def vehicle_model(self, obj):
        return obj.vehicle.model_name if obj.vehicle else "차량 정보 없음"

    @admin.display(description="작업 종류", ordering="kind")
    def kind_display(self, obj):
        return obj.get_kind_display()

    @admin.display(description="총액(원)", ordering="amount_krw")
    def amount_display(self, obj):
        return f"{obj.amount_krw:,}"

    @admin.display(description="주행거리(km)", ordering="odometer_km")
    def odometer_display(self, obj):
        return obj.odometer_km if obj.odometer_km is not None else "미등록"

    @admin.display(description="정비 내용", ordering="description")
    def description_display(self, obj):
        return obj.description or "없음"

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
