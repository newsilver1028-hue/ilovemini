from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("core", "0037_partner_service_category_option")]

    operations = [
        migrations.AddField(
            model_name="partnerbooking",
            name="cancellation_reason",
            field=models.CharField(
                blank=True,
                default="",
                max_length=500,
                verbose_name="예약 취소 사유",
            ),
        ),
    ]
