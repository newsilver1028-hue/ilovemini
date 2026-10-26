import hashlib
import html
import json
import logging
import re
import secrets
from datetime import timedelta
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.db import transaction
from django.conf import settings
from django.db.models import Avg, Count, F, Q, Sum
from django.utils import timezone
from rest_framework import permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import ScopedRateThrottle

from .integrity import ledger_record_hash, legacy_ledger_record_hash
from .models import (
    Vehicle, LedgerEntry, LedgerEvidence, Reminder, Notice, Partner, Offer, PushDevice, VehicleTransferCode,
    PartnerStaff, PartnerReview, VehicleOwnership, VehiclePlateHistory, AttendanceCheckin, PartnerBooking, RecordCorrectionRequest,
    PointTransaction, PointRedemptionRequest,
)
from .permissions import OwnerOrStaff, SafeMethodsOrStaff
from .serializers import VehicleSerializer, LedgerEntrySerializer, ReminderSerializer, NoticeSerializer, PartnerSerializer, PartnerReviewSerializer, OfferSerializer, PartnerBookingSerializer
from .vehicle_identity import normalize_plate_number

logger = logging.getLogger(__name__)


def log_naver_search_failure(operation, exc):
    """Log upstream failure details without ever logging API credentials."""
    if isinstance(exc, HTTPError):
        try:
            body = exc.read().decode("utf-8", errors="replace")
        except Exception:
            body = ""
        for credential in (settings.NAVER_API_HUB_CLIENT_ID, settings.NAVER_API_HUB_CLIENT_SECRET):
            if credential:
                body = body.replace(credential, "[redacted]")
        logger.warning("NAVER API HUB %s returned HTTP %s: %s", operation, exc.code, body[:500])
    elif isinstance(exc, URLError):
        logger.warning("NAVER API HUB %s connection failed (%s)", operation, type(exc.reason).__name__)
    else:
        logger.warning("NAVER API HUB %s failed (%s)", operation, type(exc).__name__)

class HealthView(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        from django.db import connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except Exception:
            return Response({"status": "degraded", "service": "ilovemini-api", "database": "unavailable"}, status=503)
        return Response({"status": "ok", "service": "ilovemini-api", "database": "ok"})


class CafeSearchView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "cafe_search"

    def get(self, request):
        query = str(request.query_params.get("q", "")).strip()
        if len(query) < 2 or len(query) > 80:
            return Response({"detail": "검색어는 2자 이상 80자 이하로 입력해 주세요."}, status=400)
        if not settings.NAVER_API_HUB_CLIENT_ID or not settings.NAVER_API_HUB_CLIENT_SECRET:
            return Response({"detail": "네이버 검색 API 키를 서버 환경설정에 등록해야 합니다."}, status=503)
        params = urlencode({"query": f"아이러브미니 {query}", "display": 10, "start": 1, "sort": "sim", "format": "json"})
        upstream = Request(
            "https://naverapihub.apigw.ntruss.com/search/v1/cafearticle?" + params,
            headers={
                "X-NCP-APIGW-API-KEY-ID": settings.NAVER_API_HUB_CLIENT_ID,
                "X-NCP-APIGW-API-KEY": settings.NAVER_API_HUB_CLIENT_SECRET,
                "Accept": "application/json",
            },
        )
        try:
            with urlopen(upstream, timeout=7) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            log_naver_search_failure("cafe search", exc)
            return Response({"detail": "네이버 카페 검색에 연결하지 못했습니다. 잠시 후 다시 시도해 주세요."}, status=502)

        def plain(value):
            return html.unescape(re.sub(r"<[^>]+>", "", str(value or ""))).strip()

        rows = []
        for item in payload.get("items", []):
            link = str(item.get("link", ""))
            if not link.startswith("https://cafe.naver.com/"):
                continue
            rows.append({"title": plain(item.get("title")), "description": plain(item.get("description")),
                         "link": link, "cafe_name": plain(item.get("cafename")),
                         "cafe_url": str(item.get("cafeurl", ""))})
        # Search API output is returned live; it is not persisted or sent to an AI summarizer.
        return Response({"query": query, "items": rows, "total": payload.get("total", len(rows)),
                         "source": "NAVER API HUB · 공개 카페 검색"})


class CafeLatestView(APIView):
    """Fetch recent public ILOVEMINI cafe posts through NAVER API HUB search."""
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "cafe_search"

    def get(self, request):
        if not settings.NAVER_API_HUB_CLIENT_ID or not settings.NAVER_API_HUB_CLIENT_SECRET:
            return Response({"detail": "네이버 검색 API 키를 서버 환경설정에 등록해야 합니다."}, status=503)
        params = urlencode({"query": "MINI", "display": 30, "start": 1, "sort": "date", "format": "json"})
        upstream = Request(
            "https://naverapihub.apigw.ntruss.com/search/v1/cafearticle?" + params,
            headers={
                "X-NCP-APIGW-API-KEY-ID": settings.NAVER_API_HUB_CLIENT_ID,
                "X-NCP-APIGW-API-KEY": settings.NAVER_API_HUB_CLIENT_SECRET,
                "Accept": "application/json",
            },
        )
        try:
            with urlopen(upstream, timeout=7) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            log_naver_search_failure("cafe latest", exc)
            return Response({"detail": "카페 최신글을 가져오지 못했습니다. 잠시 후 다시 시도해 주세요."}, status=502)

        def plain(value):
            return html.unescape(re.sub(r"<[^>]+>", "", str(value or ""))).strip()

        rows = []
        for item in payload.get("items", []):
            link = str(item.get("link", ""))
            if not link.startswith("https://cafe.naver.com/"):
                continue
            cafe_url = str(item.get("cafeurl", ""))
            cafe_name = plain(item.get("cafename"))
            cafe_slug = urlparse(cafe_url).path.strip("/").lower()
            if cafe_slug not in {"minilover", "ilovemini"} and cafe_name not in {"아이러브미니", "ILOVEMINI"}:
                continue
            rows.append({"title": plain(item.get("title")), "description": plain(item.get("description")),
                         "link": link, "cafe_name": cafe_name or "아이러브미니", "cafe_url": cafe_url})
            if len(rows) == 10:
                break
        return Response({"items": rows, "total": payload.get("total", len(rows)),
                         "source": "NAVER API HUB · 아이러브미니 공개글 · 최신순"})



def _attendance_payload(user, today):
    rows = list(AttendanceCheckin.objects.filter(user=user).order_by("-checkin_date")[:31])
    today_row = next((row for row in rows if row.checkin_date == today), None)
    now = timezone.now()
    balance = PointTransaction.objects.filter(user=user).aggregate(total=Sum("points_delta"))["total"] or 0
    available = PointTransaction.objects.filter(user=user, available_at__lte=now).aggregate(total=Sum("points_delta"))["total"] or 0
    return {
        "balance_points": balance,
        "available_points": available,
        "checked_in_today": today_row is not None,
        "today_points": today_row.points_awarded if today_row else 0,
        "streak_days": 0,
        "checkins": [{"date": row.checkin_date.isoformat(), "points": row.points_awarded, "streak_days": row.streak_days} for row in rows[:30]],
    }


class AttendanceView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "attendance"

    def get(self, request):
        return Response(_attendance_payload(request.user, timezone.localdate()))

    def post(self, request):
        today = timezone.localdate()
        with transaction.atomic():
            # Serialize check-in attempts for the same member to prevent concurrent duplicate awards.
            type(request.user).objects.select_for_update().get(pk=request.user.pk)
            existing = AttendanceCheckin.objects.filter(user=request.user, checkin_date=today).first()
            if existing:
                payload = _attendance_payload(request.user, today)
                payload.update({"earned_points": 0, "message": "오늘은 이미 출석했어요."})
                return Response(payload, status=status.HTTP_200_OK)
            award = 100
            now = timezone.now()
            AttendanceCheckin.objects.create(user=request.user, checkin_date=today, points_awarded=award, streak_days=1)
            PointTransaction.objects.create(
                user=request.user,
                transaction_type=PointTransaction.Type.ATTENDANCE,
                points_delta=award,
                available_at=now,
                memo=f"출석 적립 ({today})",
                idempotency_key=f"attendance:{request.user.pk}:{today.isoformat()}",
            )
        payload = _attendanc