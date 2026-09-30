import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def migrate_current_owners(apps, schema_editor):
    Vehicle = apps.get_model("core", "Vehicle")
    VehicleOwnership = apps.get_model("core", "VehicleOwnership")
    for vehicle in Vehicle.objects.exclude(owner_id__isnull=True).iterator():
        VehicleOwnership.objects.get_or_create(
            vehicle_id=vehicle.pk,
            ended_at=None,
            defaults={
                "user_id": vehicle.owner_id,
                "started_at": vehicle.created_at,
                "verification_method": "legacy_import",
                "verification_status": "user_claimed",
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0007_append_only_record_corrections"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="vehicle",
            name="manufacturer",
            field=models.CharField(default="MINI", max_length=80),
        ),
        migrations.AddField(
            model_name="vehicle",
            name="first_registration_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="vehicle",
            name="vin_hash",
            field=models.CharField(blank=True, db_index=True, max_length=64),
        ),
        migrations.AddField(
            model_name="vehicle",
            name="public_id",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.AddField(
            model_name="vehicle",
            name="passport_public",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="vehicle",
            name="status",
            field=models.CharField(default="active", max_length=16),
        ),
        migrations.CreateModel(
            name="VehicleOwnership",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("started_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("ended_at", models.DateTimeField(blank=True, null=True)),
                ("verification_method", models.CharField(default="account_registration", max_length=32)),
                ("verification_status", models.CharField(choices=[("user_claimed", "차주 등록"), ("document_verified", "서류 확인"), ("system_verified", "시스템 확인")], default="user_claimed", max_length=24)),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="vehicle_ownerships", to=settings.AUTH_USER_MODEL)),
                ("vehicle", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="ownerships", to="core.vehicle")),
            ],
            options={"ordering": ["-started_at", "-id"]},
        ),
        migrations.RunPython(migrate_current_owners, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="vehicleownership",
            constraint=models.UniqueConstraint(condition=models.Q(("ended_at__isnull", True), ("user__isnull", False)), fields=("vehicle",), name="one_active_vehicle_owner"),
        ),
        migrations.RemoveField(model_name="vehicle", name="owner"),
    ]
