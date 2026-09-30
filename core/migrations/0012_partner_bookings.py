from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0011_attendance_points_default"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="partnerstaff",
            name="can_manage_bookings",
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name="PartnerBooking",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("requested_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("scheduled_at", models.DateTimeField()),
                ("service_type", models.CharField(max_length=100)),
                ("customer_note", models.CharField(blank=True, max_length=500)),
                ("contact_phone", models.CharField(blank=True, max_length=24)),
                ("status", models.CharField(choices=[("requested", "접수 대기"), ("confirmed", "예약 확정"), ("rejected", "예약 거절"), ("cancelled", "취소"), ("completed", "완료")], default="requested", max_length=16)),
                ("partner_note", models.CharField(blank=True, max_length=500)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("customer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="partner_bookings", to=settings.AUTH_USER_MODEL)),
                ("partner", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="bookings", to="core.partner")),
                ("vehicle", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="bookings", to="core.vehicle")),
            ],
            options={"ordering": ["-requested_at"]},
        ),
        migrations.AddIndex(
            model_name="partnerbooking",
            index=models.Index(fields=["partner", "scheduled_at", "status"], name="core_partne_partner_427ead_idx"),
        ),
    ]
