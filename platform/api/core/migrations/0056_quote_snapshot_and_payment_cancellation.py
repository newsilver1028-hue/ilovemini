from django.db import migrations, models
import django.utils.timezone
from datetime import datetime, time, timedelta


def revoke_unfrozen_quote_links(apps, schema_editor):
    Share = apps.get_model("core", "PartnerQuoteShare")
    Share.objects.filter(revoked_at__isnull=True).update(revoked_at=django.utils.timezone.now())
    Payment = apps.get_model("core", "PartnerPayment")
    Payment.objects.filter(status="cancelled", cancelled_at__isnull=True).update(
        cancelled_at=models.F("created_at"), cancelled_amount_krw=models.F("amount_krw")
    )
    Close = apps.get_model("core", "PartnerDailyClose")
    for close in Close.objects.all().iterator():
        start = django.utils.timezone.make_aware(datetime.combine(close.business_date, time.min))
        end = django.utils.timezone.make_aware(datetime.combine(close.business_date + timedelta(days=1), time.min))
        sales = Payment.objects.filter(partner_id=close.partner_id, status="approved", paid_at__gte=start, paid_at__lt=end)
        totals = {row["method"]: row["total"] or 0 for row in sales.values("method").annotate(total=models.Sum("amount_krw"))}
        refunds = Payment.objects.filter(partner_id=close.partner_id, cancelled_at__gte=start, cancelled_at__lt=end).aggregate(total=models.Sum("cancelled_amount_krw"))["total"] or 0
        Close.objects.filter(pk=close.pk).update(
            expected_cash_krw=totals.get("cash", 0),
            expected_card_krw=totals.get("card", 0) + totals.get("easy_pay", 0),
            expected_transfer_krw=totals.get("transfer", 0),
            expected_refund_krw=refunds,
        )


class Migration(migrations.Migration):
    dependencies = [("core", "0055_quote_share_revision")]

    operations = [
        migrations.AddField(
            model_name="partnerquoteshare",
            name="snapshot",
            field=models.JSONField(blank=True, default=dict, verbose_name="공유 당시 견적 내용"),
        ),
        migrations.AddField(
            model_name="partnerpayment",
            name="cancelled_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="취소 처리 일시"),
        ),
        migrations.AddField(
            model_name="partnerdailyclose",
            name="expected_refund_krw",
            field=models.PositiveIntegerField(default=0, verbose_name="시스템 환불 합계(원)"),
        ),
        migrations.AddField(
            model_name="partnerdailyclose",
            name="counted_refund_krw",
            field=models.PositiveIntegerField(default=0, verbose_name="실제 환불 합계(원)"),
        ),
        migrations.AddField(
            model_name="partnerpayment",
            name="cancelled_amount_krw",
            field=models.PositiveIntegerField(default=0, verbose_name="취소 금액(원)"),
        ),
        migrations.RunPython(revoke_unfrozen_quote_links, migrations.RunPython.noop),
    ]
