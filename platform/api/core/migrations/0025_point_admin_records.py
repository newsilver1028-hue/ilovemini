import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
from django.utils import timezone


def import_attendance_history(apps, schema_editor):
    AttendanceCheckin = apps.get_model("core", "AttendanceCheckin")
    PointTransaction = apps.get_model("core", "PointTransaction")
    database = schema_editor.connection.alias
    for checkin in AttendanceCheckin.objects.using(database).iterator():
        PointTransaction.objects.using(database).get_or_create(
            idempotency_key=f"attendance:{checkin.pk}",
            defaults={
                "user_id": checkin.user_id,
                "transaction_type": "attendance",
                "points_delta": checkin.points_awarded,
                "available_at": checkin.created_at,
                "memo": f"출석 적립 ({checkin.checkin_date})",
            },
        )


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("core", "0024_ledger_evidence_images"),
    ]

    operations = [
        migrations.CreateModel(
            name="PointTransaction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("transaction_type", models.CharField(choices=[("attendance", "출석 적립"), ("service_earn", "정비 결제 적립"), ("redemption", "포인트 사용"), ("refund", "사용 취소·환급"), ("adjustment", "운영자 조정")], max_length=20, verbose_name="거래 종류")),
                ("points_delta", models.IntegerField(help_text="적립은 양수, 사용은 음수로 기록합니다.", verbose_name="포인트 변동")),
                ("available_at", models.DateTimeField(default=timezone.now, verbose_name="사용 가능 시각")),
                ("memo", models.CharField(blank=True, max_length=240, verbose_name="처리 내용")),
                ("idempotency_key", models.CharField(default=uuid.uuid4, max_length=100, unique=True, verbose_name="중복 방지 키")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="거래 시각")),
                ("ledger_entry", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="point_transactions", to="core.ledgerentry", verbose_name="정비 기록")),
                ("partner", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="point_transactions", to="core.partner", verbose_name="협력업체")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="point_transactions", to=settings.AUTH_USER_MODEL, verbose_name="회원")),
            ],
            options={"verbose_name": "포인트 거래 내역", "verbose_name_plural": "포인트 거래 내역", "ordering": ["-created_at", "-pk"]},
        ),
        migrations.CreateModel(
            name="PointRedemptionRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("payment_amount_krw", models.PositiveIntegerField(verbose_name="결제 금액(원)")),
                ("points_requested", models.PositiveIntegerField(verbose_name="사용 요청 포인트")),
                ("status", models.CharField(choices=[("pending", "승인 대기"), ("approved", "회원 승인"), ("completed", "사용 완료"), ("rejected", "회원 거절"), ("expired", "시간 만료"), ("cancelled", "업체 취소")], default="pending", max_length=16, verbose_name="처리 상태")),
                ("expires_at", models.DateTimeField(verbose_name="요청 만료 시각")),
                ("responded_at", models.DateTimeField(blank=True, null=True, verbose_name="회원 응답 시각")),
                ("completed_at", models.DateTimeField(blank=True, null=True, verbose_name="사용 완료 시각")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="요청 시각")),
                ("member", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="point_redemption_requests", to=settings.AUTH_USER_MODEL, verbose_name="회원")),
                ("partner", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="point_redemption_requests", to="core.partner", verbose_name="협력업체")),
                ("transaction", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="redemption_requests", to="core.pointtransaction", verbose_name="포인트 거래")),
            ],
            options={"verbose_name": "포인트 사용 승인 요청", "verbose_name_plural": "포인트 사용 승인 요청", "ordering": ["-created_at", "-pk"]},
        ),
        migrations.RunPython(import_attendance_history, migrations.RunPython.noop),
    ]
