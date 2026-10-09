from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("core", "0021_partner_images")]

    operations = [
        migrations.AlterField(
            model_name="pushdevice",
            name="installation_id",
            field=models.CharField(max_length=2048, unique=True),
        ),
    ]
