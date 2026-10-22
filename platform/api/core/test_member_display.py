from django.contrib import admin
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import (
    AppleIdentity,
    AttendanceCheckin,
    LedgerEntry,
    MemberPreference,
    NaverIdentity,
    Partner,
    PartnerReview,
    PartnerStaff,
    PointRedemptionRequest,
    PointTransaction,
    PushDevice,
    RecordCorrectionRequest,
    Vehicle,
    VehicleOwnership,
    VehiclePlateHistory,
    VehicleTransferCode,
)
from .naver_auth import user_for_profile
from .member_display import member_label

User = get_user_model()
class MemberDisplayTests(TestCase):
    def setUp(self):
        self.root = User.objects.create_superuser('displayadmin', 'admin@example.com', 'test-secret-9238')
        self.member = user_for_profile({'id':'display-member', 'nickname':'테스트회원', 'email':'member@example.com'})
        self.client.force_login(self.root)

    def test_profile_updates_existing_account_without_relinking(self):
        changed = user_for_profile({'id':'display-member', 'nickname':'새닉네임', 'email':'new@example.com'})
        self.assertEqual(changed.pk, self.member.pk)
        self.assertEqual(changed.email, 'new@example.com')
        self.assertIn('새닉네임', member_label(changed))
        user_for_profile({'id':'display-member'})
        changed.refresh_from_db()
        self.assertEqual(changed.email, 'new@example.com')

    def test_list_search_by_nickname_and_number(self):
        url = reverse('admin:auth_user_changelist')
        for query in ['테스트회원', str(self.member.pk), 'member@example.com']:
            response = self.client.get(url, {'q':query})
            self.assertContains(response, '테스트회원')

    def test_autocomplete_label_and_permissions(self):
        url = reverse('admin:core_partnerstaff_member_autocomplete')
        params = {'app_label':'core', 'model_name':'partnerstaff', 'field_name':'user', 'term':'테스트회원'}
        result = self.client.get(url, params)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()['results'][0]['text'], member_label(self.member))
        self.client.force_login(self.member)
        self.assertNotEqual(self.client.get(url, params).status_code, 200)

    def test_selected_account_readable(self):
        response = self.client.get(reverse('admin:core_partnerstaff_add'))
        self.assertEqual(response.status_code, 200)
        field = response.context['adminform'].form.fields['user']
        self.assertEqual(field.label_from_instance(self.member), member_label(self.member))

    def test_empty_lookup_and_pagination(self):
        response = self.client.get(reverse('admin:core_partnerstaff_member_autocomplete'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(row['id'] == str(self.member.pk) for row in response.json()['results']))
        self.assertIn('pagination', response.json())

    def test_member_table_and_csv(self):
        url = reverse('admin:auth_user_changelist')
        response = self.client.get(url)
        self.assertContains(response, '가입 회원 목록')
        self.assertContains(response, '소속 협력업체')
        response = self.client.post(url, {'action': 'export_members_csv', '_selected_action': [str(self.member.pk)]})
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/csv', response['Content-Type'])
        self.assertIn('테스트회원', response.content.decode('utf-8-sig'))

    def test_profile_name_and_existing_permissions_retained(self):
        user = user_for_profile({'id': 'display-member', 'name': '홍길동', 'nickname': '미니회원', 'email': 'mini@example.com'})
        self.assertEqual(user.pk, self.member.pk)
        self.assertEqual(user.get_full_name(), '홍길동')
        self.assertIn('홍길동', member_label(user))
        user_for_profile({'id': 'display-member'})
        user.refresh_from_db()
        self.assertEqual(user.get_full_name(), '홍길동')
        self.assertEqual(user.email, 'mini@example.com')

    def test_admin_member_columns_show_nicknames(self):
        self.assertIn('display_nickname', admin.site._registry[User].list_display)
        self.assertNotIn('username', admin.site._registry[User].list_display)
        expected = {
            VehiclePlateHistory: 'changed_by_nickname',
            VehicleOwnership: 'member_nickname',
            AttendanceCheckin: 'member',
            PointTransaction: 'member',
            PointRedemptionRequest: 'member_nickname',
            PartnerReview: 'reviewer_nickname',
            PartnerStaff: 'member_account',
            PushDevice: 'member_nickname',
            VehicleTransferCode: 'previous_owner_nickname',
            MemberPreference: 'member',
            RecordCorrectionRequest: 'member',
        }
        for model, column in expected.items():
            with self.subTest(model=model.__name__):
                self.assertIn(column, admin.site._registry[model].list_display)

    def test_member_preference_admin_search_filter_and_vehicle_label(self):
        vehicle = Vehicle.objects.create(
            model_name="MINI Cooper S", plate_number="12가3456",
        )
        VehicleOwnership.objects.create(vehicle=vehicle, user=self.member)
        preference = MemberPreference.objects.create(user=self.member, primary_vehicle=vehicle)
        MemberPreference.objects.create(user=self.root)

        changelist_url = reverse("admin:core_memberpreference_changelist")
        response = self.client.get(changelist_url, {"q": str(self.member.pk)})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "테스트회원")
        self.assertContains(response, "12가3456")

        assigned = self.client.get(changelist_url, {"vehicle_assigned": "assigned"})
        self.assertEqual(
            [row.pk for row in assigned.context["cl"].result_list],
            [preference.pk],
        )
        unassigned = self.client.get(changelist_url, {"vehicle_assigned": "unassigned"})
        self.assertEqual(
            [row.user_id for row in unassigned.context["cl"].result_list],
            [self.root.pk],
        )

        change = self.client.get(reverse("admin:core_memberpreference_change", args=[preference.pk]))
        self.assertContains(change, "12가3456 · MINI Cooper S")

    def test_member_detail_shows_readonly_apple_login_identity(self):
        AppleIdentity.objects.create(
            user=self.member,
            subject="apple-scoped-subject-987",
            email="private-relay@example.com",
            cafe_nickname="애플회원",
        )
        response = self.client.get(reverse("admin:auth_user_change", args=[self.member.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Apple 로그인 정보")
        self.assertContains(response, "애플회원")
        self.assertContains(response, "private-relay@example.com")
        self.assertContains(response, "apple-scoped-subject-987")

    def test_point_transaction_detail_uses_nickname_instead_of_login_username(self):
        partner = Partner.objects.create(name="포인트 사용 업체", branch_label="성수점", is_active=True)
        transaction = PointTransaction.objects.create(
            user=self.member,
            partner=partner,
            transaction_type=PointTransaction.Type.REDEMPTION,
            points_delta=-500,
            memo="정비 결제 포인트 사용",
        )

        response = self.client.get(
            reverse("admin:core_pointtransaction_change", args=[transaction.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "테스트회원")
        self.assertContains(response, f"회원 #{self.member.pk}")
        self.assertContains(response, "포인트 사용 업체")
        self.assertContains(response, "정비 결제 포인트 사용")
        self.assertNotContains(response, self.member.username)

    def test_point_transaction_list_renders_linked_ledger_amount_without_500(self):
        partner = Partner.objects.create(name="연결 정비 업체", branch_label="성수점")
        vehicle = Vehicle.objects.create(
            model_name="MINI Cooper", plate_number="12가3456",
        )
        entry = LedgerEntry.objects.create(
            vehicle=vehicle,
            kind=LedgerEntry.Kind.SERVICE,
            amount_krw=125000,
            odometer_km=45000,
            partner=partner,
            source=LedgerEntry.Source.PARTNER,
        )
        PointTransaction.objects.create(
            user=self.member,
            partner=partner,
            ledger_entry=entry,
            transaction_type=PointTransaction.Type.SERVICE_EARN,
            points_delta=1250,
            memo="정비 적립",
        )

        response = self.client.get(reverse("admin:core_pointtransaction_changelist"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "125,000원")
        self.assertContains(response, "45,000km")


    def test_member_detail_shows_point_totals_and_full_transaction_history(self):
        partner = Partner.objects.create(name="회원 포인트 업체", branch_label="성수점")
        PointTransaction.objects.create(
            user=self.member,
            transaction_type=PointTransaction.Type.ATTENDANCE,
            points_delta=1000,
            memo="출석 체크 적립",
        )
        PointTransaction.objects.create(
            user=self.member,
            partner=partner,
            transaction_type=PointTransaction.Type.SERVICE_EARN,
            points_delta=750,
            memo="정비 결제 적립",
        )
        PointTransaction.objects.create(
            user=self.member,
            partner=partner,
            transaction_type=PointTransaction.Type.REDEMPTION,
            points_delta=-500,
            memo="업체 결제 포인트 사용",
        )

        response = self.client.get(reverse("admin:auth_user_change", args=[self.member.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "포인트 요약")
        self.assertContains(response, "누적 적립")
        self.assertContains(response, "1,750P")
        self.assertContains(response, "누적 사용")
        self.assertContains(response, "500P")
        self.assertContains(response, "전체 포인트 거래 내역")
        self.assertContains(response, "출석 체크 적립")
        self.assertContains(response, "정비 결제 적립")
        self.assertContains(response, "업체 결제 포인트 사용")
        self.assertContains(response, "회원 포인트 업체")


    def test_point_transaction_calendar_shows_daily_earned_and_spent_totals(self):
        PointTransaction.objects.create(
            user=self.member,
            transaction_type=PointTransaction.Type.ATTENDANCE,
            points_delta=1750,
            memo="날짜별 적립 합계 테스트",
        )
        PointTransaction.objects.create(
            user=self.member,
            transaction_type=PointTransaction.Type.REDEMPTION,
            points_delta=-500,
            memo="날짜별 사용 합계 테스트",
        )
        response = self.client.get(reverse("admin:core_pointtransaction_changelist"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["show_calendar"])
        self.assertEqual(response.context["calendar_field_label"], "등록 시각")
        self.assertContains(response, "1,750P 적립")
        self.assertContains(response, "500P 사용")
        self.assertEqual(response.content.decode().count("class=\\\"partner-calendar partner-calendar--mini admin-mini-calendar\\\""), 1)
