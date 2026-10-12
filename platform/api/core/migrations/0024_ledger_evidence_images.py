import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("core", "0023_naveridentity_cafe_nickname")]

    operations = [
        migrations.AlterField(
            model_name="ledgerentry",
            name="kind",
            field=models.CharField(
                choices=[
                    ("fuel", "주유"),
                    ("service", "정비·소모품"),
                    ("part", "정비·소모품"),
                    ("wash", "세차"),
                    ("bodywork", "판금·도색·보험처리"),
                    ("wheel_tire", "휠·타이어"),
                    ("other", "기타"),
                ],
                max_length=16,
            ),
        ),
        migrations.CreateModel(
            name="LedgerEvidence",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("image_data", models.BinaryField(editable=False)),
                ("content_type", models.CharField(editable=False, max_length=32)),
                ("file_name", models.CharField(blank=True, max_length=180)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "entry",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="evidence_image",
                        to="core.ledgerentry",
                    ),
                ),
            ],
            options={
                "verbose_name": "정비기록 첨부 사진",
                "verbose_name_plural": "정비기록 첨부 사진",
            },
        ),
    ]
