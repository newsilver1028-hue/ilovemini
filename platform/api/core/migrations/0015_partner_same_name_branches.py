from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0014_vehicle_use_relationship"),
    ]

    operations = [
        migrations.AddField(
            model_name="partner",
            name="branch_label",
            field=models.CharField(blank=True, default="", max_length=80),
        ),
        migrations.AlterField(
            model_name="partner",
            name="name",
            field=models.CharField(max_length=120),
        ),
        migrations.AddConstraint(
            model_name="partner",
            constraint=models.UniqueConstraint(fields=("name", "branch_label"), name="unique_partner_name_branch"),
        ),
    ]
