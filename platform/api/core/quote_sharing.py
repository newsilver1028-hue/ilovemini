from datetime import timedelta

from django.http import Http404, JsonResponse
from django.db import transaction
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_GET

from .models import PartnerQuoteShare, PartnerWorkOrder, ServiceEstimate
from .member_display import member_nickname


def work_order_quote_context(work_order, document_type="quote"):
    titles = {"quote": "정비 견적서", "job-card": "정비 작업지시서", "repair-statement": "정비 명세서", "receipt": "수납 영수증"}
    lines = list(work_order.lines.all())
    items = [{"title": line.description, "amount_krw": line.amount_krw, "quantity": line.quantity, "unit": line.unit, "unit_price_krw": line.unit_price_krw} for line in lines]
    if not items:
        items = work_order.items if isinstance(work_order.items, list) else []
    total = work_order.final_total_krw if document_type in {"repair-statement", "receipt"} else (work_order.quoted_total_krw or sum(item.get("amount_krw", 0) for item in items if isinstance(item, dict) and type(item.get("amount_krw")) is int))
    customer = work_order.customer
    vehicle = work_order.partner_vehicle or work_order.vehicle
    return {
        "work_order_id": work_order.pk,
        "document_title": titles[document_type], "document_type": document_type,
        "document_number": f"WO-{work_order.created_at:%y%m%d}-{work_order.pk:05d}",
        "issued_at": work_order.updated_at, "partner": work_order.partner,
        "customer_name": work_order.customer_name or (customer.name if customer else ""),
        "contact_phone": work_order.contact_phone or (customer.phone if customer else ""),
        "vehicle_model": work_order.vehicle_model or (vehicle.model_name if vehicle else "미입력"),
        "plate_number": work_order.plate_number or (vehicle.plate_number if vehicle else "미입력"),
        "odometer_km": work_order.odometer_km, "customer_concern": work_order.customer_concern,
        "inspection_notes": work_order.inspection_notes, "items": items, "total_krw": total,
        "paid_krw": work_order.paid_amount_krw, "balance_krw": max(0, total - work_order.paid_amount_krw),
        "work_notes": work_order.work_notes, "note": work_order.customer_message, "status": work_order.get_status_display(),
    }


def estimate_quote_context(estimate):
    booking = estimate.booking
    vehicle = booking.vehicle
    return {
        "document_title": "정비 견적서", "document_type": "quote",
        "document_number": f"EST-{booking.pk:06d}-{estimate.revision:02d}",
        "issued_at": estimate.created_at, "partner": booking.partner,
        "customer_name": member_nickname(booking.customer), "contact_phone": booking.contact_phone,
        "vehicle_model": vehicle.model_name if vehicle else "미입력",
        "plate_number": vehicle.plate_number if vehicle else "미입력",
        "odometer_km": vehicle.current_odometer_km if vehicle else None,
        "customer_concern": booking.customer_note, "inspection_notes": "", "items": estimate.items if isinstance(estimate.items, list) else [],
        "total_krw": estimate.total_krw, "tax_included": True, "note": estimate.note, "status": estimate.get_status_display(),
    }


def quote_snapshot(context):
    """Freeze customer-visible quote values at issuance time."""
    partner = context["partner"]
    return {
        key: value.isoformat() if hasattr(value, "isoformat") else value
        for key, value in {
            **context,
            "partner_name": partner.name,
            "partner_branch_label": partner.branch_label,
            "partner_phone": partner.phone,
            "partner_address": partner.address,
            "partner_business_info": partner.business_info,
            "partner_representative_name": partner.representative_name,
            "partner_kakao_channel_url": partner.kakao_channel_url,
        }.items()
        if key != "partner"
    }


def create_quote_share(request, *, work_order=None, estimate=None):
    if request.method != "POST":
        return JsonResponse({"detail": "POST 요청만 허용됩니다."}, status=405)
    with transaction.atomic():
        if work_order:
            work_order = PartnerWorkOrder.objects.select_for_update().get(pk=work_order.pk)
            if work_order.status in (PartnerWorkOrder.Status.COMPLETED, PartnerWorkOrder.Status.CANCELLED):
                return JsonResponse({"detail": "완료·취소된 작업에는 새 견적 링크를 만들 수 없습니다."}, status=409)
            # Only the newest quote revision remains actionable.
            work_order.quote_shares.filter(revoked_at__isnull=True).update(revoked_at=timezone.now())
            work_order.quote_revision += 1
            work_order.quote_status = PartnerWorkOrder.QuoteStatus.SENT
            work_order.quote_responded_at = None
            work_order.quote_decline_reason = ""
            work_order.status = PartnerWorkOrder.Status.WAITING_APPROVAL
            work_order.save(update_fields=("quote_revision", "quote_status", "quote_responded_at", "quote_decline_reason", "status", "updated_at"))
        snapshot_context = work_order_quote_context(work_order) if work_order else estimate_quote_context(estimate)
        share = PartnerQuoteShare.objects.create(
            work_order=work_order, estimate=estimate, created_by=request.user,
            quote_revision=work_order.quote_revision if work_order else 0,
            snapshot=quote_snapshot(snapshot_context),
            expires_at=timezone.now() + timedelta(days=3),
        )
    from django.urls import reverse
    url = request.build_absolute_uri(reverse("public_partner_quote", args=[share.token]))
    response = JsonResponse({"url": url, "expires_in_days": 3})
    response["Cache-Control"] = "private, no-store"
    return response


def public_partner_quote(request, token):
    if request.method not in ("GET", "POST"):
        return JsonResponse({"detail": "GET 또는 POST 요청만 허용됩니다."}, status=405)
    share = PartnerQuoteShare.objects.filter(
        token=token, revoked_at__isnull=True, expires_at__gt=timezone.now(),
    ).select_related(
        "work_order__partner", "work_order__customer", "work_order__vehicle", "work_order__partner_vehicle",
        "estimate__booking__partner", "estimate__booking__vehicle", "estimate__booking__customer",
    ).first()
    if not share:
        raise Http404
    decision_message = ""
    if request.method == "POST":
        if not share.work_order_id:
            raise Http404
        decision = request.POST.get("decision")
        if decision not in ("approved", "declined"):
            decision_message = "응답을 선택해 주세요."
        else:
            with transaction.atomic():
                work_order = PartnerWorkOrder.objects.select_for_update().get(pk=share.work_order_id)
                current_share = PartnerQuoteShare.objects.select_for_update().filter(pk=share.pk).first()
                if (
                    not current_share
                    or current_share.expires_at <= timezone.now()
                    or current_share.revoked_at
                    or current_share.quote_revision != work_order.quote_revision
                    or work_order.quote_status != PartnerWorkOrder.QuoteStatus.SENT
                ):
                    decision_message = "이 견적 링크는 만료되었거나 이미 응답 처리되었습니다. 업체에 새 견적을 요청해 주세요."
                else:
                    work_order.quote_status = decision
                    work_order.quote_responded_at = timezone.now()
                    work_order.quote_decline_reason = request.POST.get("decline_reason", "").strip()[:500] if decision == "declined" else ""
                    work_order.status = PartnerWorkOrder.Status.IN_PROGRESS if decision == "approved" else PartnerWorkOrder.Status.QUOTE
                    work_order.save(update_fields=("quote_status", "quote_responded_at", "quote_decline_reason", "status", "updated_at"))
                    decision_message = "견적을 승인했습니다." if decision == "approved" else "견적 거절 의견을 업체에 전달했습니다."
    if share.work_order_id:
        context = dict(share.snapshot) if share.snapshot else work_order_quote_context(share.work_order)
        if share.snapshot:
            from datetime import datetime
            if context.get("issued_at"):
                context["issued_at"] = datetime.fromisoformat(context["issued_at"])
            context["partner"] = type("PartnerSnapshot", (), {
                "name": context.pop("partner_name", ""),
                "branch_label": context.pop("partner_branch_label", ""),
                "phone": context.pop("partner_phone", ""),
                "address": context.pop("partner_address", ""),
                "business_info": context.pop("partner_business_info", ""),
                "representative_name": context.pop("partner_representative_name", ""),
                "kakao_channel_url": context.pop("partner_kakao_channel_url", ""),
            })()
        context["quote_status"] = PartnerWorkOrder.objects.only("quote_status").get(pk=share.work_order_id).quote_status
    else:
        context = dict(share.snapshot) if share.snapshot else estimate_quote_context(share.estimate)
        if share.snapshot:
            from datetime import datetime
            if context.get("issued_at"):
                context["issued_at"] = datetime.fromisoformat(context["issued_at"])
            context["partner"] = type("PartnerSnapshot", (), {
                "name": context.pop("partner_name", ""),
                "branch_label": context.pop("partner_branch_label", ""),
                "phone": context.pop("partner_phone", ""),
                "address": context.pop("partner_address", ""),
                "business_info": context.pop("partner_business_info", ""),
                "representative_name": context.pop("partner_representative_name", ""),
                "kakao_channel_url": context.pop("partner_kakao_channel_url", ""),
            })()
        context["quote_status"] = share.estimate.status
    context["decision_message"] = decision_message
    context["public_share"] = True
    response = render(request, "core/partner_quote_print.html", context)
    response["Cache-Control"] = "private, no-store"
    response["X-Robots-Tag"] = "noindex, nofollow, noarchive"
    response["Referrer-Policy"] = "no-referrer"
    return response
