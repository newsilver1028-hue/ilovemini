from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0043_banner_asset_options"),
    ]

    operations = [
        migrations.AddField(
            model_name="seasonbanner",
            name="image_data",
            field=models.BinaryField(blank=True, null=True, editable=False),
        ),
        migrations.AddField(
            model_name="seasonbanner",
            name="image_content_type",
            field=models.CharField(blank=True, editable=False, max_length=32),
        ),
        migrations.AddField(
            model_name="appcontent",
            name="image_data",
            field=models.BinaryField(blank=True, null=True, editable=False),
        ),
        migrations.AddField(
            model_name="appcontent",
            name="image_content_type",
            field=models.CharField(blank=True, editable=False, max_length=32),
        ),
        migrations.AddField(
            model_name="partner",
            name="storefront_photo_data",
            field=models.BinaryField(blank=True, null=True, editable=False),
        ),
        migrations.AddField(
            model_name="partner",
            name="storefront_photo_content_type",
            field=models.CharField(blank=True, editable=False, max_length=32),
        ),
        migrations.AddField(
            model_name="partner",
            name="representative_photo_data",
            field=models.BinaryField(blank=True, null=True, editable=False),
        ),
        migrations.AddField(
            model_name="partner",
            name="representative_photo_content_type",
            field=models.CharField(blank=True, editable=False, max_length=32),
        ),
    ]
