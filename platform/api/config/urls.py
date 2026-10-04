from core.season_views import SeasonBannerView
from core.app_views import AppContentView, ShoppingSearchView, MemberPreferenceView, MemberOverviewView, PassportPreviewView, RecordCorrectionView, ResolveCorrectionView
from rest_framework_simplejwt.views import TokenRefreshView
from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from core.views import HealthView, CafeSearchView, CafeLatestView, CafeAnswerView, VehicleViewSet, LedgerEntryViewSet, ReminderViewSet, NoticeViewSet, PartnerViewSet, OfferViewSet, PushDeviceView, AttendanceView, PartnerBookingViewSet
from core.member_views import MemberGradeView
from core.auth_views import NaverStartView, NaverCallbackView, NaverCompleteView

router = DefaultRouter()
router.register("vehicles", VehicleViewSet, basename="vehicle")
router.register("ledger", LedgerEntryViewSet, basename="ledger")
router.register("reminders", ReminderViewSet, basename="reminder")
router.register("notices", NoticeViewSet, basename="notice")
router.register("partners", PartnerViewSet, basename="partner")
router.register("offers", OfferViewSet, basename="offer")
router.register("bookings", PartnerBookingViewSet, basename="booking")
urlpatterns = [
    path("api/app/content/", AppContentView.as_view(), name="app_content"),
    path("api/shopping/search/", ShoppingSearchView.as_view(), name="shopping_search"),
    path("api/me/preferences/", MemberPreferenceView.as_view(), name="member_preferences"),
    path("api/me/overview/", MemberOverviewView.as_view(), name="member_overview"),
    path("api/vehicles/preview-passport/", PassportPreviewView.as_view(), name="passport_preview"),
    path("api/record-corrections/", RecordCorrectionView.as_view(), name="record_corrections"),
    path("api/record-corrections/<int:pk>/resolve/", ResolveCorrectionView.as_view(), name="resolve_correction"),
    path("api/app/season-banner/", SeasonBannerView.as_view(), name="season_banner"),
    path("admin/", admin.site.urls),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/me/grade/", MemberGradeView.as_view(), name="member_grade"),
    path("api/health/", HealthView.as_view(), name="health"),
    path("api/cafe/search/", CafeSearchView.as_view(), name="cafe_search"),
    path("api/cafe/latest/", CafeLatestView.as_view(), name="cafe_latest"),
    path("api/cafe/answer/", CafeAnswerView.as_view(), name="cafe_answer"),
    path("api/auth/naver/start/", NaverStartView.as_view(), name="naver_start"),
    path("api/auth/naver/callback/", NaverCallbackView.as_view(), name="naver_callback"),
    path("api/auth/naver/complete/", NaverCompleteView.as_view(), name="naver_complete"),
    path("api/push/devices/", PushDeviceView.as_view(), name="push_devices"),
    path("api/attendance/", AttendanceView.as_view(), name="attendance"),
    path("api/", include(router.urls)),
]
