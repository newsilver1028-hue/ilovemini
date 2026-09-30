import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0009_partner_qr_registration"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AttendanceCheckin",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("checkin_date", models.DateField()),
                ("points_awarded", models.PositiveIntegerField(default=10)),
                ("streak_days", models.PositiveSmallIntegerField(default=1)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attendance_checkins", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-checkin_date"]},
        ),
        migrations.AddConstraint(
            model_name="attendancecheckin",
            constraint=models.UniqueConstraint(fields=("user", "checkin_date"), name="unique_user_daily_checkin"),
        ),
    ]
