import json
from datetime import time
from pathlib import Path
from django.core import serializers
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from core.models import Partner, PartnerWeeklySchedule


class Command(BaseCommand):
    help = "전체 업체의 기본 주간 예약 시간을 매일 09:00~18:00으로 설정합니다. 기본은 미리보기이며 날짜별 휴무·예약 차단은 변경하지 않습니다."

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true')
        parser.add_argument('--backup-path')

    def handle(self, *args, **options):
        if not options['apply']:
            self.stdout.write(json.dumps({'dry_run': True, 'partners': Partner.objects.count(), 'weekdays': 7, 'opens_at': '09:00', 'closes_at': '18:00'}, ensure_ascii=False))
            return
        if not options['backup_path']:
            raise CommandError('--apply에는 변경 전 운영시간을 저장할 --backup-path가 필요합니다.')
        with transaction.atomic():
            partners = list(Partner.objects.select_for_update().order_by('pk'))
            before = PartnerWeeklySchedule.objects.select_for_update().order_by('partner_id', 'weekday')
            snapshot = {'captured_at': timezone.now().isoformat(), 'partner_ids': [p.pk for p in partners], 'weekly_schedules': json.loads(serializers.serialize('json', before))}
            path = Path(options['backup_path'])
            path.parent.mkdir(parents=True, exist_ok=True)
            # Refuse to overwrite the rollback snapshot on a retry.
            with path.open('x', encoding='utf-8') as file:
                json.dump(snapshot, file, ensure_ascii=False)
            path.chmod(0o600)
            created = updated = unchanged = 0
            for partner in partners:
                for weekday in range(7):
                    row, new = PartnerWeeklySchedule.objects.get_or_create(partner=partner, weekday=weekday, defaults={'opens_at':time(9), 'closes_at':time(18), 'is_closed':False, 'slot_interval_minutes':30})
                    if new:
                        created += 1
                    elif row.opens_at != time(9) or row.closes_at != time(18) or row.is_closed:
                        row.opens_at, row.closes_at, row.is_closed = time(9), time(18), False
                        row.save(update_fields=['opens_at','closes_at','is_closed'])
                        updated += 1
                    else:
                        unchanged += 1
            valid = PartnerWeeklySchedule.objects.filter(partner_id__in=[p.pk for p in partners], weekday__range=(0,6), opens_at=time(9), closes_at=time(18), is_closed=False).count()
            if valid != len(partners)*7:
                raise CommandError('운영시간 검증 실패: 변경을 롤백했습니다.')
        self.stdout.write(json.dumps({'applied':True,'partners':len(partners),'created':created,'updated':updated,'unchanged':unchanged,'verified_days':valid,'exceptions_and_blocks':'unchanged'},ensure_ascii=False))
