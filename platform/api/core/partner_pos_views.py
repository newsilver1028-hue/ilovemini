import hashlib
import hmac
import json
from datetime import datetime

from django.db import transaction
from django.db.models import Sum
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import PartnerPayment, PartnerPosIntegration, PartnerWorkOrder


MAX_EVENT_BYTES = 16 * 1024


@csrf_exempt
@require_POST
def partner_pos_event(request):
    """Receive normalized POS payment events; this does not initiate card charges."""
    if len(request.body) > MAX_EVENT_BYTES:
        return JsonResponse({"detail": "요청 크기가 너무 큽니다."}, status=413)
    authorization = request.headers.get("Authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return JsonResponse({"detail": "인증 토큰이 필요합니다."}, status=401)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    integration = PartnerPosIntegration.objects.filter(token_hash=token_hash, is_active=True).select_related("partner").first()
    if not integration or not hmac.compare_digest(integration.token_hash, token_hash):
        return JsonResponse({"detail": "유효하지 않은 POS 연동 토큰입니다."}, status=401)
    if request.content_type != "application/json":
        return JsonResponse({"detail": "application/json 요청만 지원합니다."}, status=415)
    try:
        event = json.loads(request.body)
    except (TypeError, ValueError):
        return JsonResponse({"detail": "JSON 형식을 확인해 주세요."}, status=400)
    if not isinstance(event, dict):
        return JsonResponse({"detail": "JSON 객체가 필요합니다."}, status=400)

    transaction_id = str(event.get("event_id", "")).strip()
    work_order_id = event.get("work_order_id")
    event_status = event.get("status")
    if not transaction_id or len(transaction_id) > 120 or not str(work_order_id or "").isdigit():
        return JsonResponse({"detail": "event_id와 work_order_id가 필요합니다."}, status=400)
    if event_status not in ("approved", "cancelled"):
        return JsonResponse({"detail": "status는 approved 또는 cancelled여야 합니다."}, status=400)

    with transaction.atomic():
        integration = PartnerPosIntegration.objects.select_for_update().filter(
            pk=integration.pk, token_hash=token_hash, is_active=True
        ).select_related("partner").first()
        if not integration:
            return JsonResponse({"detail": "유효하지 않은 POS 연동 토큰입니다."}, status=401)
        order = PartnerWorkOrder.objects.select_for_update().filter(
            pk=work_order_id, partner_id=integration.partner_id
        ).first()
        if not order:
            return JsonResponse({"detail": "작업을 찾을 수 없습니다."}, status=404)
        existing = PartnerPayment.objects.select_for_update().filter(
            partner_id=integration.partner_id,
            provider_name=integration.provider_name or "POS",
            provider_transaction_id=transaction_id,
        ).first()
        previous_pos_total = PartnerPayment.objects.filter(
            work_order=order, status=PartnerPayment.Status.APPROVED
        ).aggregate(total=Sum("amount_krw"))["total"] or 0
        if event_status == "approved":
            method = event.get("method")
            amount = event.get("amount_krw")
            if method not in PartnerPayment.Method.values or type(amount) is not int or amount <= 0:
                return JsonResponse({"detail": "method 또는 amount_krw 값이 올바르지 않습니다."}, status=400)
            if existing:
                if existing.work_order_id != order.pk or existing.amount_krw != amount or existing.method != method:
                    return JsonResponse({"detail": "이미 처리된 거래와 내용이 다릅니다."}, status=409)
                integration.last_received_at = timezone.now()
                integration.save(update_fields=("last_received_at", "updated_at"))
                return JsonResponse({"ok": True, "duplicate": True, "payment_id": existing.pk})
            try:
                paid_at = datetime.fromisoformat(str(event.get("paid_at", "")).replace("Z", "+00:00")) if event.get("paid_at") else timezone.now()
                if timezone.is_naive(paid_at):
                    paid_at = timezone.make_aware(paid_at)
            except (TypeError, ValueError):
                return JsonResponse({"detail": "paid_at은 ISO-8601 형식이어야 합니다."}, status=400)
            payment = PartnerPayment.objects.create(
                partner_id=integration.partner_id,
                work_order=order,
                provider_name=integration.provider_name or "POS",
                provider_transaction_id=transaction_id,
                method=method,
                amount_krw=amount,
                approval_code=str(event.get("approval_code", ""))[:80],
                paid_at=paid_at,
            )
        else:
            if not existing or existing.work_order_id != order.pk:
                return JsonResponse({"detail": "취소할 승인 거래를 찾을 수 없습니다."}, status=404)
            if existing.status == PartnerPayment.Status.CANCELLED:
                integration.last_received_at = timezone.now()
                integration.save(update_fields=("last_received_at", "updated_at"))
                return JsonResponse({"ok": True, "duplicate": True, "payment_id": existing.pk})
            existing.status = PartnerPayment.Status.CANCELLED
            existing.save(update_fields=("status",))
            payment = existing

        # Keep payments entered manually in the work order while syncing POS totals.
        manual_paid_amount = max(0, order.paid_amount_krw - previous_pos_total)
        totals = PartnerPayment.objects.filter(
            work_order=order, status=PartnerPayment.Status.APPROVED
        ).aggregate(total=Sum("amount_krw"))
        new_pos_total = totals["total"] or 0
        order.paid_amount_krw = manual_paid_amount + new_pos_total
        methods = list(PartnerPayment.objects.filter(
            work_order=order, status=PartnerPayment.Status.APPROVED
        ).values_list("method", flat=True).distinct()[:2])
        if not order.paid_amount_krw:
            order.payment_method = ""
        elif manual_paid_amount == 0:
            order.payment_method = methods[0] if len(methods) == 1 else ""
        order.save(update_fields=("paid_amount_krw", "payment_method", "updated_at"))
        integration.last_received_at = timezone.now()
        integration.save(update_fields=("last_received_at", "updated_at"))
        return JsonResponse({"ok": True, "duplicate": False, "payment_id": payment.pk, "paid_amount_krw": order.paid_amount_krw})
