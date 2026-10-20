from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0034_appleidentity"),
    ]

    operations = [
        migrations.AddField(
            model_name="appleidentity",
            name="cafe_nickname",
            field=models.CharField(blank=True, max_length=40, verbose_name="카페 닉네임"),
        ),
    ]
