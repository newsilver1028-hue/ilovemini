from django.db import migrations, models
import django.core.validators

def initial_setting(apps, schema_editor):
    apps.get_model('core','AppRuntimeSettings').objects.using(schema_editor.connection.alias).get_or_create(pk=1)

class Migration(migrations.Migration):
    dependencies = [('core','0041_naveroauthattempt_flow')]
    operations = [migrations.CreateModel(name='AppRuntimeSettings', fields=[
        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
        ('refresh_interval_seconds',models.PositiveSmallIntegerField(default=15, verbose_name='사용 중 변경 확인 주기(초)', validators=[django.core.validators.MinValueValidator(10),django.core.validators.MaxValueValidator(120)])),
        ('show_demo_products',models.BooleanField(default=True, verbose_name='상품 미등록 시 데모 이미지 표시')),
        ('public_revision',models.PositiveBigIntegerField(default=1,editable=False)),
        ('member_revision',models.PositiveBigIntegerField(default=1,editable=False)),
    ],options={'verbose_name':'앱 연동 설정','verbose_name_plural':'앱 연동 설정'}),
        migrations.RunPython(initial_setting,migrations.RunPython.noop)]
