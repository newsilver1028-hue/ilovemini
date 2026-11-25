from datetime import datetime, time, timedelta

from django.db.models import Sum
from django.utils import timezone

from .models import PartnerDailyClose, PartnerPayment


def refresh_daily_close_expected(partner_id, day):
    """Reconcile a day's POS sales and refunds after late webhook events."""
    tz = timezone.get_current_timezone()
    start = timezone.make_aware(datetime.combine(day, time.min), tz)
    end = timezone.make_aware(datetime.combine(day + timedelta(days=1), time.min), tz)
    sales = PartnerPayment.objects.filter(
        partner_id=partner_id,
        status=PartnerPayment.Status.APPROVED,
        paid_at__gte=start,
        paid_at__lt=end,
    ).values("method").annotate(total=Sum("amount_krw"))
    totals = {row["method"]: row["total"] or 0 for row in sales}
    refunds = PartnerPayment.objects.filter(
        partner_id=partner_id,
        cancelled_at__gte=start,
        cancelled_at__lt=end,
    ).aggregate(total=Sum("cancelled_amount_krw"))["total"] or 0
    PartnerDailyClose.objects.filter(partner_id=partner_id, business_date=day).update(
        expected_cash_krw=totals.get(PartnerPayment.Method.CASH, 0),
        expected_card_krw=totals.get(PartnerPayment.Method.CARD, 0) + totals.get(PartnerPayment.Method.EASY_PAY, 0),
        expected_transfer_krw=totals.get(PartnerPayment.Method.TRANSFER, 0),
        expected_refund_krw=refunds,
    )
