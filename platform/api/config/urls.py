from core.phase_one_views import RecommendationViewSet, EstimateViewSet
from core.season_views import SeasonBannerView
from core.app_views import AppContentView, ShoppingSearchView, MemberPreferenceView, MemberOverviewView, PassportPreviewView, RecordCorrectionView, ResolveCorrectionView, CompleteCorrectionView
from rest_framework_simplejwt.views import TokenRefreshView
from django.contrib import admin
from django.urls import include, path
from django.http import HttpResponseRedirect
from django.conf import settings
from django.views.generic import RedirectView
from rest_framework.routers import DefaultRouter
from core.views import HealthView, CafeSearchView, CafeLatestView, VehicleViewSet, LedgerEntryViewSet, ReminderViewSet, NoticeViewSet, PartnerViewSet, OfferViewSet, PushDeviceView, AttendanceView, PartnerBookingViewSet, PartnerPointRedemptionView, PartnerPointBalanceView, MemberPointRedemptionView
from core.member_views import MemberGradeView
from core.auth_views import NaverStartView, NaverCallbackView, NaverCompleteView, AppleLoginView, AppReviewLoginView, AccountDeletionView, PartnerNaverLoginStartView, PartnerNaverLoginCompleteView
from core.partner_admin import partner_admin_site
from core.privacy_views import privacy_policy, terms_of_service
from core.partner_push_views import web_push_subscribe, web_push_unsubscribe, partner_service_worker
from core.partner_pos_views import partner_pos_event
from core.media_views import app_content_image, season_banner_image, partner_image

router = DefaultRouter()
from core.app_sync import AppSyncView, MemberPointHistoryView
router.register("maintenance-recommendations", RecommendationViewSet, basename="maintenance-recommendation")
router.register("service-estimates", EstimateViewSet, basename="service-estimate")
router.register("vehicles", VehicleViewSet, basename="vehicle")
router.register("ledger", LedgerEntryViewSet, basename="ledger")
router.register("reminders", ReminderViewSet, basename="reminder")
router.register("notices", NoticeViewSet, basename="notice")
router.register("partners", PartnerViewSet, basename="partner")
router.register("offers", OfferViewSet, basename="offer")
router.register("bookings", PartnerBookingViewSet, basename="booking")


def public_home(request):
    host = request.get_host().split(":", 1)[0].lower()
    if host == settings.ADMIN_CUSTOM_DOMAIN:
        return HttpResponseRedirect("/partner-admin/login/")
    return HttpResponseRedirect("/privacy/")


urlpatterns = [
    path("", public_home, name="public_home"),
    path("partner/", RedirectView.as_view(url="/partner-admin/login/", permanent=False), name="partner_admin_shortcut"),
    path("privacy/", privacy_policy, name="privacy_policy"),
    path("terms/", terms_of_service, name="terms_of_service"),
    path("api/app/content/", AppContentView.as_view(), name="app_content"),
    path("api/media/app-content/<int:pk>/", app_content_image, name="app_content_image"),
    path("api/media/season-banner/<int:pk>/", season_banner_image, name="season_banner_image"),
    path("api/media/partners/<int:pk>/<str:image_kind>/", partner_image, name="partner_uploaded_image"),
    path("api/app/sync/", AppSyncView.as_view(), name="app_sync"),
    path("api/points/history/", MemberPointHistoryView.as_view(), name="member_point_history"),
    path("api/shopping/search/", ShoppingSearchView.as_view(), name="shopping_search"),
    path("api/me/preferences/", MemberPreferenceView.as_view(), name="member_preferences"),
    path("api/me/overview/", MemberOverviewView.as_view(), name="member_overview"),
    path("api/vehicles/preview-passport/", PassportPreviewView.as_view(), name="passport_preview"),
    path("api/record-corrections/", RecordCorrectionView.as_view(), name="record_corrections"),
    path("api/record-corrections/<int:pk>/resolve/", ResolveCorrectionView.as_view(), name="resolve_correction"),
    path("api/record-corrections/<int:pk>/complete/", CompleteCorrectionView.as_view(), name="complete_correction"),
    path("api/app/season-banner/", SeasonBannerView.as_view(), name="season_banner"),
    path("admin/", admin.site.urls),
    path("partner-admin/naver/start/", PartnerNaverLoginStartView.as_view(), name="partner_naver_start"),
    path("partner-admin/naver/complete/", PartnerNaverLoginCompleteView.as_view(), name="partner_naver_complete"),
    path("partner-admin/push/subscribe/", web_push_subscribe, name="partner_web_push_subscribe"),
    path("partner-admin/push/unsubscribe/", web_push_unsubscribe, name="partner_web_push_unsubscribe"),
    path("api/partner-pos/events/", partner_pos_event, name="partner_pos_event"),
    path("partner-admin/service-worker.js", partner_service_worker, name="partner_service_worker"),
    path("partner-admin/", partner_admin_site.urls),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/me/grade/", MemberGradeView.as_view(), name="member_grade"),
    path("api/health/", HealthView.as_view(), name="health"),
    path("api/cafe/search/", CafeSearchView.as_view(), name="cafe_search"),
    path("api/cafe/latest/", CafeLatestView.as_view(), name="cafe_latest"),
    path("api/auth/naver/start/", NaverStartView.as_view(), name="naver_start"),
    path("api/auth/naver/callback/", NaverCallbackView.as_view(), name="naver_callback"),
    path("api/auth/naver/complete/", NaverCompleteView.as_view(), name="naver_complete"),
    path("api/auth/apple/", AppleLoginView.as_view(), name="apple_login"),
    path("api/auth/review-login/", AppReviewLoginView.as_view(), name="review_login"),
    path("api/me/account/", AccountDeletionView.as_view(), name="account_delete"),
    path("api/push/devices/", PushDeviceView.as_view(), name="push_devices"),
    path("api/attendance/", AttendanceView.as_view(), name="attendance"),
    path("api/points/balance/", PartnerPointBalanceView.as_view(), name="partner_point_balance"),
    path("api/points/redemptions/", PartnerPointRedemptionView.as_view(), name="partner_point_redemptions"),
    path("api/points/redemptions/pending/", MemberPointRedemptionView.as_view(), name="member_pending_point_redemption"),
    path("api/points/redemptions/<int:pk>/respond/", MemberPointRedemptionView.as_view(), name="member_respond_point_redemption"),
    path("api/", include(router.urls)),
]
