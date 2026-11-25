import io
import json
import tempfile
from datetime import time, date
from pathlib import Path
from django.contrib.auth import get_user_model
from django.core.management import call_command, CommandError
from django.test import TestCase
from core.models import Partner, PartnerStaff, PartnerPart, PartnerStockMovement, PartnerWeeklySchedule, PartnerScheduleException


class StockAndDefaultHoursTests(TestCase):
    def setUp(self):
        self.partner = Partner.objects.create(name='검수용 업체',is_active=True)
        self.user = get_user_model().objects.create_user('qa-stock')
        PartnerStaff.objects.create(user=self.user,partner=self.partner,is_active=True,can_manage_bookings=True)
        PartnerWeeklySchedule.objects.all().delete()
        self.part = PartnerPart.objects.create(partner=self.partner,name='검수 부품',stock_quantity=1)
        self.client.force_login(self.user)

    def outbound(self, quantity):
        return self.client.post('/partner-admin/core/partnerstockmovement/add/', {'partner':self.partner.pk,'part':self.part.pk,'direction':'out','reason':'adjustment','quantity':quantity,'note':'격리 검수','_save':'저장'})

    def test_overdraw_is_field_error_without_stock_change(self):
        response = self.outbound(2)
        self.assertEqual(response.status_code,200)
        self.assertContains(response,'현재고는 1개입니다.')
        self.assertIn('quantity',response.context['adminform'].form.errors)
        self.part.refresh_from_db()
        self.assertEqual(self.part.stock_quantity,1)
        self.assertFalse(PartnerStockMovement.objects.exists())

    def test_valid_outbound_then_second_attempt_is_rejected(self):
        self.assertEqual(self.outbound(1).status_code,302)
        self.part.refresh_from_db()
        self.assertEqual(self.part.stock_quantity,0)
        self.assertEqual(PartnerStockMovement.objects.count(),1)
        response=self.outbound(1)
        self.assertEqual(response.status_code,200)
        self.assertContains(response,'현재고는 0개입니다.')
        self.assertEqual(PartnerStockMovement.objects.count(),1)

    def test_default_hours_require_explicit_apply_and_backup(self):
        call_command('set_default_partner_hours',stdout=io.StringIO())
        self.assertFalse(PartnerWeeklySchedule.objects.exists())
        with self.assertRaises(CommandError):
            call_command('set_default_partner_hours',apply=True,stdout=io.StringIO())

    def test_all_partners_get_seven_days_and_preserve_exceptions(self):
        other=Partner.objects.create(name='비활성 검수업체',is_active=False)
        PartnerWeeklySchedule.objects.filter(partner=other).delete()
        row=PartnerWeeklySchedule.objects.create(partner=self.partner,weekday=0,opens_at=time(10),closes_at=time(17),slot_interval_minutes=60,is_closed=True)
        exception=PartnerScheduleException.objects.create(partner=self.partner,date=date(2026,12,25),is_closed=True)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'before.json'
            call_command('set_default_partner_hours',apply=True,backup_path=str(path),stdout=io.StringIO())
            snapshot=json.loads(path.read_text())
            self.assertEqual(len(snapshot['weekly_schedules']),1)
            self.assertEqual(snapshot['weekly_schedules'][0]['fields']['opens_at'],'10:00:00')
            self.assertEqual(PartnerWeeklySchedule.objects.count(),14)
            self.assertEqual(PartnerWeeklySchedule.objects.filter(opens_at=time(9),closes_at=time(18),is_closed=False).count(),14)
            row.refresh_from_db();exception.refresh_from_db()
            self.assertEqual(row.slot_interval_minutes,60)
            self.assertTrue(exception.is_closed)
            call_command('set_default_partner_hours',apply=True,backup_path=str(Path(directory)/'second.json'),stdout=io.StringIO())
            self.assertEqual(PartnerWeeklySchedule.objects.count(),14)
