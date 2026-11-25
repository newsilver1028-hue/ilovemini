import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0052_alter_partnerweeklyschedule_closes_at_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="partner",
            name="kakao_channel_url",
            field=models.URLField(blank=True, help_text="예: https://pf.kakao.com/_채널ID/chat", max_length=2048, verbose_name="카카오톡 채널 상담 주소"),
        ),
        migrations.CreateModel(
            name="PartnerQuoteShare",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("token", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField(db_index=True)),
                ("revoked_at", models.DateTimeField(blank=True, null=True)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ("estimate", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="quote_shares", to="core.serviceestimate")),
                ("work_order", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="quote_shares", to="core.partnerworkorder")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddConstraint(
            model_name="partnerquoteshare",
            constraint=models.CheckConstraint(
                condition=(models.Q(work_order__isnull=False, estimate__isnull=True) | models.Q(work_order__isnull=True, estimate__isnull=False)),
                name="partner_quote_share_exactly_one_source",
            ),
        ),
    ]
