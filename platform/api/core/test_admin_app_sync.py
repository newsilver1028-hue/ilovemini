from datetime import timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from .models import AppRuntimeSettings, AppContent, Partner, PartnerImage, PointTransaction, Notice, MemberPreference, Vehicle, VehicleOwnership

class AdminAppSyncTests(TestCase):
    def setUp(self):
        self.client=APIClient()
        self.setting,_=AppRuntimeSettings.objects.get_or_create(pk=1)
        self.member=get_user_model().objects.create_user(username='sync-member')
        self.other=get_user_model().objects.create_user(username='sync-other')

    def test_admin_save_changes_shared_revision_after_commit(self):
        before=self.client.get('/api/app/sync/').data['public_revision']
        with self.captureOnCommitCallbacks(execute=True):
            AppContent.objects.create(title='배너',kind='banner',is_active=True)
        response=self.client.get('/api/app/sync/')
        self.assertNotEqual(before,response.data['public_revision'])
        self.assertEqual(response['Cache-Control'],'private, no-store')
        self.assertIsNone(response.data['member_revision'])

    def test_member_changes_are_not_returned_to_anonymous_clients(self):
        self.client.force_authenticate(self.member)
        before=self.client.get('/api/app/sync/').data['member_revision']
        with self.captureOnCommitCallbacks(execute=True):
            PointTransaction.objects.create(user=self.member,transaction_type='adjustment',points_delta=10)
        self.assertNotEqual(before,self.client.get('/api/app/sync/').data['member_revision'])
        self.client.force_authenticate(None)
        self.assertIsNone(self.client.get('/api/app/sync/').data['member_revision'])

    def test_scheduled_expiry_changes_revision_without_a_save(self):
        item=AppContent.objects.create(title='기간 배너',kind='banner',is_active=True,ends_at=timezone.now()+timedelta(hours=1))
        before=self.client.get('/api/app/sync/').data['public_revision']
        AppContent.objects.filter(pk=item.pk).update(ends_at=timezone.now()-timedelta(seconds=1))
        self.assertNotEqual(before,self.client.get('/api/app/sync/').data['public_revision'])

    def test_image_replacement_changes_url_for_same_image_record(self):
        partner=Partner.objects.create(name='사진 업체',is_active=True)
        image=PartnerImage.objects.create(partner=partner,image_data=b'first',content_type='image/png')
        before=self.client.get(f'/api/partners/{partner.pk}/').data['introduction_images'][0]['url']
        image.image_data=b'second';image.save()
        after=self.client.get(f'/api/partners/{partner.pk}/').data['introduction_images'][0]['url']
        self.assertNotEqual(before,after)

    def test_products_can_be_shown_without_purchase_links(self):
        item=AppContent(title='미리보기',kind='product',category='recommended',is_active=True,asset_key='grille-parts')
        item.full_clean();item.save()
        response=self.client.get('/api/app/content/')
        self.assertEqual([row['id'] for row in response.data['products']],[item.pk])
        self.assertEqual(response.data['products'][0]['action_url'],'')

    def test_admin_can_disable_demo_and_change_refresh_interval(self):
        self.setting.show_demo_products=False;self.setting.refresh_interval_seconds=30;self.setting.save()
        data=self.client.get('/api/app/content/').data
        self.assertFalse(data['configuration']['show_demo_products'])
        self.assertEqual(self.client.get('/api/app/sync/').data['configuration']['refresh_interval_seconds'],30)

    def test_point_history_is_scoped_and_includes_partner_and_reason(self):
        partner=Partner.objects.create(name='정비 업체',is_active=True)
        PointTransaction.objects.create(user=self.member,partner=partner,transaction_type='redemption',points_delta=-500,memo='정비 결제 사용')
        PointTransaction.objects.create(user=self.other,transaction_type='adjustment',points_delta=9999,memo='다른 회원')
        self.assertEqual(self.client.get('/api/points/history/').status_code,401)
        self.client.force_authenticate(self.member)
        response=self.client.get('/api/points/history/')
        rows=response.data['results'] if isinstance(response.data,dict) else response.data
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['points_delta'],-500)
        self.assertEqual(rows[0]['partner_name'],'정비 업체')
        self.assertEqual(rows[0]['memo'],'정비 결제 사용')
        self.assertIn('created_at',rows[0])

    def test_primary_vehicle_preference_is_scoped_to_current_owner(self):
        vehicle=Vehicle.objects.create(model_name='MINI',status='active')
        VehicleOwnership.objects.create(vehicle=vehicle,user=self.member)
        MemberPreference.objects.create(user=self.member,primary_vehicle=vehicle)
        self.client.force_authenticate(self.member)
        self.assertEqual(self.client.get('/api/me/preferences/').data['primary_vehicle_id'],vehicle.pk)
        self.client.force_authenticate(self.other)
        self.assertIsNone(self.client.get('/api/me/preferences/').data['primary_vehicle_id'])
