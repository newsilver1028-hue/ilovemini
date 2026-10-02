import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0012_partner_bookings"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="vehicle",
            name="plate_number",
            field=models.CharField(blank=True, db_index=True, default="", max_length=16),
        ),
        migrations.AddConstraint(
            model_name="vehicle",
            constraint=models.UniqueConstraint(
                condition=models.Q(status="active") & ~models.Q(plate_number=""),
                fields=("plate_number",),
                name="uniq_active_vehicle_plate",
            ),
        ),
        migrations.CreateModel(
            name="VehiclePlateHistory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("plate_number", models.CharField(max_length=16)),
                ("started_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("ended_at", models.DateTimeField(blank=True, null=True)),
                ("changed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="vehicle_plate_changes", to=settings.AUTH_USER_MODEL)),
                ("vehicle", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="plate_history", to="core.vehicle")),
            ],
            options={"ordering": ["-started_at", "-id"]},
        ),
        migrations.AddConstraint(
            model_name="vehicleplatehistory",
            constraint=models.UniqueConstraint(
                condition=models.Q(("ended_at__isnull", True)),
                fields=("plate_number",),
                name="uniq_current_plate_history",
            ),
        ),
    ]
