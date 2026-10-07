from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [("core", "0020_partner_profile_reviews")]
    operations = [migrations.CreateModel(
        name="PartnerImage",
        fields=[("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("caption", models.CharField(blank=True, max_length=160, verbose_name="이미지 설명")),
                ("image_data", models.BinaryField(editable=False)),
                ("content_type", models.CharField(editable=False, max_length=32)),
                ("display_order", models.PositiveSmallIntegerField(default=0, verbose_name="표시 순서")),
                ("partner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="introduction_images", to="core.partner"))],
        options={"ordering": ["display_order", "pk"], "verbose_name": "업체 소개 이미지", "verbose_name_plural": "업체 소개 이미지"},
    )]
