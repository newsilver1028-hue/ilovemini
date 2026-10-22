from django.db import migrations, models


DEFAULT_CATEGORIES = [
    "경정비",
    "사고수리",
    "오디오",
    "차량유리",
    "휠.타이어",
    "전장튜닝",
    "신차패키지",
    "썬팅",
    "PPF",
    "디테일링",
]


def seed_service_categories(apps, schema_editor):
    Category = apps.get_model("core", "PartnerServiceCategoryOption")
    for order, name in enumerate(DEFAULT_CATEGORIES, start=10):
        Category.objects.get_or_create(
            name=name,
            defaults={"display_order": order * 10, "is_active": True},
        )


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0036_vehicle_retention_expires_at"),
    ]

    operations = [
        migrations.CreateModel(
            name="PartnerServiceCategoryOption",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=80, unique=True, verbose_name="서비스 분야")),
                ("is_active", models.BooleanField(default=True, verbose_name="사용")),
                ("display_order", models.PositiveSmallIntegerField(default=100, verbose_name="표시 순서")),
            ],
            options={
                "verbose_name": "업체 서비스 분야",
                "verbose_name_plural": "업체 서비스 분야",
                "ordering": ["display_order", "name"],
            },
        ),
        migrations.RunPython(seed_service_categories, migrations.RunPython.noop),
    ]
