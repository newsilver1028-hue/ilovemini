import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0006_verified_service_history"),
    ]

    operations = [
        migrations.AddField(
            model_name="ledgerentry",
            name="corrects",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="corrections",
                to="core.ledgerentry",
            ),
        ),
        migrations.AddField(
            model_name="ledgerentry",
            name="correction_reason",
            field=models.CharField(blank=True, max_length=240),
        ),
    ]
