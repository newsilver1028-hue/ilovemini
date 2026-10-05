from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0019_initial_app_content"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(model_name="partner", name="business_info", field=models.TextField(blank=True)),
        migrations.AddField(model_name="partner", name="representative_experience_years", field=models.PositiveSmallIntegerField(blank=True, null=True)),
        migrations.AddField(model_name="partner", name="representative_name", field=models.CharField(blank=True, max_length=100)),
        migrations.AddField(model_name="partner", name="representative_photo_url", field=models.URLField(blank=True, max_length=2048)),
        migrations.AddField(model_name="partner", name="representative_title", field=models.CharField(blank=True, max_length=100)),
        migrations.AddField(model_name="partner", name="storefront_photo_url", field=models.URLField(blank=True, max_length=2048)),
        migrations.CreateModel(
            name="PartnerReview",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("rating", models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])),
                ("comment", models.CharField(blank=True, max_length=1000)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("partner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="reviews", to="core.partner")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="partner_reviews", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at", "-id"]},
        ),
        migrations.AddConstraint(model_name="partnerreview", constraint=models.UniqueConstraint(fields=("partner", "user"), name="unique_partner_review_user")),
    ]
