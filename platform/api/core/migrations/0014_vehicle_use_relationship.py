from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0013_vehicle_plate_identity"),
    ]

    operations = [
        migrations.AddField(
            model_name="vehicleownership",
            name="relationship",
            field=models.CharField(
                choices=[
                    ("owned", "자가 차량"),
                    ("lease", "리스 차량"),
                    ("rental", "렌트 차량"),
                    ("family", "가족 차량"),
                    ("other", "기타 이용 차량"),
                ],
                default="owned",
                max_length=16,
            ),
        ),
        migrations.AlterField(
            model_name="vehicleownership",
            name="verification_status",
            field=models.CharField(
                choices=[
                    ("user_claimed", "사용자 등록·소유 미확인"),
                    ("document_verified", "서류 확인"),
                    ("system_verified", "시스템 확인"),
                ],
                default="user_claimed",
                max_length=24,
            ),
        ),
    ]
