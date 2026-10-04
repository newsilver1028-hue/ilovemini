from django.db import migrations, models
import django.utils.timezone

class Migration(migrations.Migration):
    dependencies = [("core", "0016_naver_full_profile")]
    operations = [migrations.CreateModel(
        name="SeasonBanner",
        fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("title", models.CharField("시즌 제목", max_length=140)),
            ("subtitle", models.CharField("안내 문구", max_length=240, blank=True)),
            ("image_url", models.URLField("배너 이미지 주소", max_length=2048, blank=True, help_text="공개 HTTPS 이미지 주소. 비워두면 기본 MINI 시작 화면을 사용합니다.")),
            ("is_active", models.BooleanField("노출 활성화", default=False)),
            ("starts_at", models.DateTimeField("노출 시작", default=django.utils.timezone.now)),
            ("ends_at", models.DateTimeField("노출 종료", null=True, blank=True)),
            ("duration_seconds", models.PositiveSmallIntegerField("표시 시간(초)", default=3)),
            ("priority", models.PositiveSmallIntegerField("우선순위", default=100, help_text="낮은 숫자부터 표시합니다.")),
        ],
        options={"verbose_name": "앱 시작 시즌 배너", "verbose_name_plural": "앱 시작 시즌 배너", "ordering": ["priority", "-starts_at", "-pk"]},
    )]
