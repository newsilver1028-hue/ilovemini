from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("core", "0022_pushdevice_fcm_token_length")]

    operations = [
        migrations.AddField(
            model_name="naveridentity",
            name="cafe_nickname",
            field=models.CharField(blank=True, max_length=40, verbose_name="네이버 카페 닉네임"),
        ),
    ]
