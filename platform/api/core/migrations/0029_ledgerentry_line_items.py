from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0027_multi_ledger_evidence_and_electrical_kind"),
    ]

    operations = [
        migrations.AddField(
            model_name="ledgerentry",
            name="line_items",
            field=models.JSONField(blank=True, default=list, verbose_name="정비 항목별 금액"),
        ),
    ]
