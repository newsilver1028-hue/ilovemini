from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("core", "0038_partnerbooking_cancellation_reason")]

    operations = [
        migrations.AlterModelOptions(
            name="memberpreference",
            options={"verbose_name": "회원 앱 설정", "verbose_name_plural": "회원 앱 설정"},
        ),
        migrations.AddField(
            model_name="ledgerentry",
            name="gross_amount_krw",
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name="정비 총액(포인트 차감 전, 원)"),
        ),
        migrations.AddField(
            model_name="ledgerentry",
            name="payment_method",
            field=models.CharField(
                blank=True,
                choices=[
                    ("card", "카드"),
                    ("cash", "현금"),
                    ("transfer", "계좌이체"),
                    ("easy_pay", "간편결제"),
                    ("mixed", "복합결제"),
                    ("points_only", "포인트 전액"),
                    ("other", "기타"),
                ],
                default="",
                max_length=16,
                verbose_name="결제 수단",
            ),
        ),
    ]
