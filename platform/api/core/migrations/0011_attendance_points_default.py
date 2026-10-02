from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("core", "0010_attendancecheckin")]

    operations = [
        migrations.AlterField(
            model_name="attendancecheckin",
            name="points_awarded",
            field=models.PositiveIntegerField(default=1000),
        ),
    ]
