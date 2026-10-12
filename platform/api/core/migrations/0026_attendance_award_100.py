from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("core", "0025_point_admin_records")]

    operations = [
        migrations.AlterField(
            model_name="attendancecheckin",
            name="points_awarded",
            field=models.PositiveIntegerField(default=100),
        ),
    ]
