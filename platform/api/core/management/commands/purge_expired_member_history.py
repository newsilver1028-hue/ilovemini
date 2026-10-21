from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from core.models import (
    LedgerEntry,
    LedgerEvidence,
    PointTransaction,
    RecordCorrectionRequest,
    Vehicle,
)


class Command(BaseCommand):
    help = "탈퇴 회원 인증 정비 이력의 1년 보관 기간이 지난 차량 자료를 파기합니다."

    def handle(self, *args, **options):
        expired_ids = list(Vehicle.objects.filter(
            retention_expires_at__lte=timezone.now(),
        ).values_list("pk", flat=True))
        purged = 0
        for vehicle_id in expired_ids:
            with transaction.atomic():
                vehicle = Vehicle.objects.select_for_update().filter(
                    pk=vehicle_id,
                    retention_expires_at__lte=timezone.now(),
                ).first()
                if vehicle is None:
                    continue
                if vehicle.ownerships.filter(user__isnull=False, ended_at__isnull=True).exists():
                    self.stderr.write(f"현재 이용자가 있는 차량 {vehicle.pk}은 파기하지 않습니다.")
                    continue
                entry_ids = list(vehicle.ledger_entries.values_list("pk", flat=True))
                if entry_ids:
                    RecordCorrectionRequest.objects.filter(
                        entry_id__in=entry_ids,
                    ).delete()
                    RecordCorrectionRequest.objects.filter(
                        resolved_entry_id__in=entry_ids,
                    ).delete()
                    PointTransaction.objects.filter(
                        ledger_entry_id__in=entry_ids,
                    ).update(ledger_entry=None)
                    LedgerEvidence.objects.filter(entry_id__in=entry_ids).delete()
                    LedgerEntry.objects.filter(pk__in=entry_ids).update(corrects=None)
                    LedgerEntry.objects.filter(pk__in=entry_ids).delete()
                vehicle.delete()
                purged += 1
        self.stdout.write(self.style.SUCCESS(
            f"파기 완료: 차량 및 인증 정비 이력 {purged}건",
        ))
