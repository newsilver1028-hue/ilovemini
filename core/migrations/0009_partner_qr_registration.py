from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0008_vehicle_passport_ownership"),
    ]

    operations = [
        migrations.DeleteModel(name="VehicleServiceCode"),
    ]
