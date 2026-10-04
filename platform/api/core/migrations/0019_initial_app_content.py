from datetime import datetime, timezone
from django.db import migrations


def seed(apps, schema_editor):
    Banner = apps.get_model('core', 'SeasonBanner')
    Content = apps.get_model('core', 'AppContent')
    start = datetime(2026, 9, 30, 15, tzinfo=timezone.utc)
    end = datetime(2026, 10, 31, 15, tzinfo=timezone.utc)
    title = 'DEUTSCH MOTORS 10월 프로모션'
    if not Banner.objects.exists():
        Banner.objects.create(title=title, asset_key='mini-october', is_active=True,
            starts_at=start, ends_at=end, duration_seconds=3)
    if not Content.objects.filter(kind='banner').exists():
        Content.objects.create(title=title, kind='banner', asset_key='mini-october',
            is_active=True, starts_at=start, ends_at=end)
    for order, (name, asset) in enumerate([
        ('차량용 거치대', 'phone-holder'), ('프런트 그릴 파츠', 'grille-parts'), ('기어 노브·부츠', 'shift-knob')
    ]):
        Content.objects.get_or_create(kind='product', title=name, defaults={
            'asset_key': asset, 'display_order': order,
            'description': '구매 주소·가격·호환 차량을 확인하고 공개해 주세요.', 'is_active': False,
        })


class Migration(migrations.Migration):
    dependencies = [('core', '0018_appcontent_apprelease_seasonbanner_asset_key_and_more')]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
