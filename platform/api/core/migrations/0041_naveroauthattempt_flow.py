from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0040_maintenancerecommendation_serviceestimate"),
    ]

    operations = [
        migrations.AddField(
            model_name="naveroauthattempt",
            name="flow",
            field=models.CharField(
                choices=[("app", "앱 로그인"), ("partner_admin", "협력업체 관리자 로그인")],
                default="app",
                max_length=20,
            ),
        ),
    ]
