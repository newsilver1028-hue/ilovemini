import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0044_admin_uploaded_images"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="naveroauthattempt",
            name="partner",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="naver_login_attempts", to="core.partner"),
        ),
        migrations.CreateModel(
            name="PartnerAccessRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("pending", "승인 대기"), ("approved", "승인"), ("rejected", "반려")], default="pending", max_length=12, verbose_name="처리 상태")),
                ("can_verify_records", models.BooleanField(default=False, verbose_name="정비기록 인증 권한")),
                ("can_manage_bookings", models.BooleanField(default=False, verbose_name="예약 관리 권한")),
                ("reviewed_at", models.DateTimeField(blank=True, null=True, verbose_name="처리 일시")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="신청 일시")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="수정 일시")),
                ("partner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="access_requests", to="core.partner", verbose_name="신청 업체")),
                ("reviewed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="reviewed_partner_access_requests", to=settings.AUTH_USER_MODEL, verbose_name="처리 관리자")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="partner_access_requests", to=settings.AUTH_USER_MODEL, verbose_name="네이버 계정")),
            ],
            options={
                "verbose_name": "협력업체 권한 신청",
                "verbose_name_plural": "협력업체 권한 신청",
                "ordering": ["status", "-created_at", "-id"],
            },
        ),
        migrations.AddConstraint(
            model_name="partneraccessrequest",
            constraint=models.UniqueConstraint(fields=("partner", "user"), name="unique_partner_access_request"),
        ),
    ]
