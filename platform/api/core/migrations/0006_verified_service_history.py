import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0005_vehicletransfercode"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="ledgerentry",
            name="source",
            field=models.CharField(choices=[("owner", "차주 입력"), ("partner", "협력업체 인증")], default="owner", max_length=16),
        ),
        migrations.AddField(model_name="ledgerentry", name="part_number", field=models.CharField(blank=True, max_length=120)),
        migrations.AddField(model_name="ledgerentry", name="evidence_url", field=models.URLField(blank=True)),
        migrations.AddField(model_name="ledgerentry", name="record_hash", field=models.CharField(blank=True, editable=False, max_length=64)),
        migrations.AddField(model_name="ledgerentry", name="verified_at", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(
            model_name="ledgerentry",
            name="partner",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="verified_ledger_entries", to="core.partner"),
        ),
        migrations.AddField(
            model_name="ledgerentry",
            name="verified_by",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="verified_ledger_entries", to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name="VehicleServiceCode",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code_digest", models.CharField(max_length=64, unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField()),
                ("used_at", models.DateTimeField(blank=True, null=True)),
                ("invalidated_at", models.DateTimeField(blank=True, null=True)),
                ("issued_by", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="issued_service_codes", to=settings.AUTH_USER_MODEL)),
                ("vehicle", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="service_codes", to="core.vehicle")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="PartnerStaff",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("can_verify_records", models.BooleanField(default=False)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("partner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="staff_members", to="core.partner")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="partner_memberships", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddConstraint(
            model_name="partnerstaff",
            constraint=models.UniqueConstraint(fields=("partner", "user"), name="unique_partner_staff"),
        ),
    ]
