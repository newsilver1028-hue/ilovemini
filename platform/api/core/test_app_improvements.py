from datetime import timedelta
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from .models import AppContent, AppRelease, SeasonBanner, Vehicle, VehicleOwnership, Partner, PartnerStaff, NaverIdentity, LedgerEntry, RecordCorrectionRequest
from .integrity import ledger_record_hash

User = get_user_model()


class AppContentTests(TestCase):
    def setUp(self):
        AppContent.objects.all().delete()
        SeasonBanner.objects.all().delete()
        self.client = APIClient()

    def test_publication_period_and_real_purchase_links(self):
        now = timezone.now()
        AppContent.objects.create(kind='product', title='비공개')
        AppContent.objects.create(kind='banner', title='종료', is_active=True, ends_at=now-timedelta(seconds=1))
        AppContent.objects.create(kind='banner', title='미래', is_active=True, starts_at=now+timedelta(days=1))
        AppContent.objects.create(kind='product', title='주소 없음', is_active=True)
        AppContent.objects.create(kind='product', title='HTTP', is_active=True, action_url='http://example.test')
        live = AppContent.objects.create(kind='product', title='판매 중', is_active=True,
            action_url='https://example.test/item', price_krw=32000)
        response = self.client.get('/api/app/content/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual([row['id'] for row in response.data['products']], [live.pk])
        self.assertEqual(response.data['products'][0]['price_krw'], 32000)
        self.assertEqual(response.data['banners'], [])
        self.assertEqual(response['Cache-Control'], 'no-store')

    def test_publish_requires_https_and_valid_dates(self):
        for row in [AppContent(kind='product', title='주소 없음', is_active=True),
                    AppContent(kind='banner', title='HTTP', image_url='http://example.test/a.png'),
                    AppContent(kind='banner', title='날짜', starts_at=timezone.now(), ends_at=timezone.now()-timedelta(days=1))]:
            with self.assertRaises(ValidationError): row.full_clean()
        with self.assertRaises(ValidationError):
            AppRelease(platform='ios', version='0.2.1', build_number=201, is_active=True).full_clean()

    def test_disabled_season_never_reappears(self):
        SeasonBanner.objects.create(title='꺼진 배너', asset_key='mini-october', is_active=False)
        self.assertIsNone(self.client.get('/api/app/season-banner/').data['banner'])

    def test_expired_banner_and_disabled_release_are_hidden(self):
        SeasonBanner.objects.create(title='종료', is_active=True, ends_at=timezone.now()-timedelta(seconds=1))
        AppRelease.objects.create(platform='ios', version='0.3.0', build_number=300,
            is_active=False, download_url='https://example.test/update')
        self.assertIsNone(self.client.get('/api/app/season-banner/').data['banner'])
        self.assertEqual(self.client.get('/api/app/content/').data['releases'], [])

    def test_deploy_sync_preserves_operator_changes(self):
        Partner.objects.all().delete()
        row = Partner.objects.create(name='랩스타모터스', region='운영자 수정 지역', service_categories=['운영자 분류'], is_active=False)
        call_command('sync_ilovemini_partners', verbosity=0)
        row.refresh_from_db()
        self.assertEqual(Partner.objects.count(), 1)
        self.assertEqual(row.region, '운영자 수정 지역')
        self.assertFalse(row.is_active)


class PrivateAppFlowTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user('owner')
        self.other = User.objects.create_user('other')
        self.staff = User.objects.create_user('staff')
        self.jcw = self.vehicle(self.owner, 'JCW', '12가3456')
        self.q4 = self.vehicle(self.owner, 'Q4', '34나5678')
        self.foreign = self.vehicle(self.other, '타인 차량', '56다7890')
        self.partner = Partner.objects.create(name='정비 업체', is_active=True)
        self.permission = PartnerStaff.objects.create(partner=self.partner, user=self.staff, is_active=True, can_verify_records=True)
        self.client = APIClient(); self.client.force_authenticate(self.owner)
        self.worker = APIClient(); self.worker.force_authenticate(self.staff)

    def vehicle(self, user, name, plate):
        row = Vehicle.objects.create(manufacturer='MINI', model_name=name, plate_number=plate)
        VehicleOwnership.objects.create(vehicle=row, user=user)
        return row

    def record(self):
        row = LedgerEntry.objects.create(vehicle=self.jcw, source='partner', partner=self.partner,
            verified_by=self.staff, verified_at=timezone.now(), kind='service', entry_date=timezone.localdate(),
            odometer_km=10000, amount_krw=100000, description='오일 교환')
        row.record_hash = ledger_record_hash(row); row.save(update_fields=['record_hash'])
        return row

    def payload(self, entry=None, **extra):
        value = {'partner': self.partner.pk, 'vehicle_public_id': str(self.jcw.public_id),
            'plate_number': self.jcw.plate_number, 'kind': 'service', 'entry_date': str(timezone.localdate()),
            'odometer_km': 10000, 'amount_krw': 120000, 'description': '오일 교환'}
        if entry: value.update(corrects=entry.pk, correction_reason='금액 정정')
        value.update(extra); return value

    def test_private_endpoints_require_login(self):
        client = APIClient()
        for url in ['/api/me/preferences/', '/api/me/overview/', '/api/record-corrections/']:
            self.assertEqual(client.get(url).status_code, 401)

    def test_primary_vehicle_shared_and_foreign_vehicle_rejected(self):
        self.assertEqual(self.client.patch('/api/me/preferences/', {'primary_vehicle_id': self.q4.pk}, format='json').status_code, 200)
        second = APIClient(); second.force_authenticate(self.owner)
        self.assertEqual(second.get('/api/me/preferences/').data['primary_vehicle_id'], self.q4.pk)
        self.assertEqual(second.patch('/api/me/preferences/', {'primary_vehicle_id': self.foreign.pk}, format='json').status_code, 404)

    def test_primary_selection_heals_after_handover(self):
        self.client.patch('/api/me/preferences/', {'primary_vehicle_id': self.q4.pk}, format='json')
        self.q4.ownerships.update(ended_at=timezone.now())
        self.assertEqual(self.client.get('/api/me/preferences/').data['primary_vehicle_id'], self.jcw.pk)

    def test_qr_preview_requires_active_partner_permission(self):
        data = {'vehicle_public_id': str(self.jcw.public_id)}
        self.assertEqual(self.client.post('/api/vehicles/preview-passport/', data, format='json').status_code, 403)
        response = self.worker.post('/api/vehicles/preview-passport/', data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('owner', response.data); self.assertNotIn('email', response.data)
        self.partner.is_active=False; self.partner.save()
        self.assertEqual(self.worker.post('/api/vehicles/preview-passport/', data, format='json').status_code, 403)

    def test_physical_plate_mismatch_prevents_registration(self):
        response = self.worker.post('/api/ledger/partner-verified/', self.payload(plate_number='90라1234'), format='json')
        self.assertEqual(response.status_code, 409)
        self.assertEqual(LedgerEntry.objects.count(), 0)

    def test_own_correction_request_is_idempotent_and_private(self):
        row = self.record(); payload = {'entry_id': row.pk, 'reason': '금액 확인 부탁드립니다'}
        self.assertEqual(self.client.post('/api/record-corrections/', payload, format='json').status_code, 201)
        self.assertEqual(self.client.post('/api/record-corrections/', payload, format='json').status_code, 200)
        client=APIClient(); client.force_authenticate(self.other)
        self.assertEqual(client.post('/api/record-corrections/', payload, format='json').status_code, 404)
        self.assertEqual(client.get('/api/record-corrections/').data, [])

    def test_linked_correction_preserves_original_and_resolves_request(self):
        row = self.record(); old_hash=row.record_hash
        self.client.post('/api/record-corrections/', {'entry_id': row.pk, 'reason': '금액'}, format='json')
        response=self.worker.post('/api/ledger/partner-verified/', self.payload(row), format='json')
        self.assertEqual(response.status_code, 201, response.data)
        corrected=LedgerEntry.objects.get(pk=response.data['id'])
        row.refresh_from_db(); self.assertEqual(row.record_hash, old_hash); self.assertEqual(row.amount_krw, 100000)
        self.assertEqual(corrected.corrects_id, row.pk)
        self.assertIsNotNone(RecordCorrectionRequest.objects.get(entry=row).resolved_at)
        summary = self.client.get(f'/api/vehicles/{row.vehicle_id}/maintenance-summary/')
        self.assertEqual(summary.data['last_maintenance']['id'], corrected.pk)
        self.assertEqual(self.worker.post('/api/ledger/partner-verified/', self.payload(row), format='json').status_code, 409)
        self.assertEqual(self.worker.post('/api/ledger/partner-verified/', self.payload(row, amount_krw=130000), format='json').status_code, 409)
        self.assertEqual(self.worker.post('/api/ledger/partner-verified/', self.payload(corrected, amount_krw=130000), format='json').status_code, 201)

    def test_pending_requests_only_issuer_workplace(self):
        row=self.record(); self.client.post('/api/record-corrections/', {'entry_id': row.pk, 'reason': '확인'}, format='json')
        self.assertEqual(len(self.worker.get('/api/record-corrections/?workplace=1').data), 1)
        self.assertEqual(self.client.get('/api/record-corrections/?workplace=1').data, [])

    def test_inherited_record_cannot_be_requested_or_corrected(self):
        row=self.record(); self.client.post('/api/record-corrections/', {'entry_id': row.pk, 'reason': '확인'}, format='json')
        request=RecordCorrectionRequest.objects.get(entry=row)
        self.jcw.ownerships.update(ended_at=timezone.now())
        VehicleOwnership.objects.create(vehicle=self.jcw, user=self.other)
        buyer=APIClient(); buyer.force_authenticate(self.other)
        self.assertEqual(buyer.post('/api/record-corrections/', {'entry_id': row.pk, 'reason': '이전 기록'}, format='json').status_code, 403)
        self.assertEqual(self.client.get('/api/record-corrections/').data, [])
        self.assertEqual(self.worker.get('/api/record-corrections/?workplace=1').data, [])
        self.assertEqual(self.worker.post(f'/api/record-corrections/{request.pk}/resolve/', {'resolved_entry_id': row.pk}, format='json').status_code, 404)
        self.assertEqual(self.worker.post('/api/ledger/partner-verified/', self.payload(row), format='json').status_code, 400)

    def test_real_member_identity_and_counts(self):
        NaverIdentity.objects.create(user=self.owner, subject='owner-subject', nickname='미니 오너')
        self.record()
        data=self.client.get('/api/me/overview/').data
        self.assertEqual(data['nickname'], '미니 오너'); self.assertEqual(data['member_id'], self.owner.pk)
        self.assertEqual(data['vehicle_count'], 2); self.assertEqual(data['verified_record_count'], 1)

    def test_ended_ownership_prevents_preview_and_registration(self):
        self.jcw.ownerships.update(ended_at=timezone.now())
        self.assertEqual(self.worker.post('/api/vehicles/preview-passport/', {'vehicle_public_id': str(self.jcw.public_id)}, format='json').status_code, 404)
        self.assertEqual(self.worker.post('/api/ledger/partner-verified/', self.payload(), format='json').status_code, 400)
        self.assertEqual(LedgerEntry.objects.count(), 0)
