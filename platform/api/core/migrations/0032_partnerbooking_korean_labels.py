from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("core", "0031_merge_line_items_and_review_account")]

    operations = [
        migrations.AlterModelOptions(
            name="partnerbooking",
            options={"ordering": ["-requested_at"], "verbose_name": "업체 예약", "verbose_name_plural": "업체 예약"},
        ),
    ]
