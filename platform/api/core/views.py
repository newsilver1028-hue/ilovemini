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
    Vehicle, LedgerEntry, Reminder, Notice, Partner, Offer, PushDevice, VehicleTransferCode,
    PartnerStaff, PartnerReview, VehicleOwnership, VehiclePlateHistory, AttendanceCheckin, PartnerBooking, RecordCorrectionRequest,
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


class CafeAnswerView(APIView):
    """Search public ILOVEMINI Cafe pages on demand and answer with citations."""
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "cafe_answer"

    def post(self, request):
        query = str(request.data.get("q", "")).strip()
        if len(query) < 2 or len(query) > 120:
            return Response({"detail": "질문은 2자 이상 120자 이하로 입력해 주세요."}, status=400)
        if not settings.OPENAI_API_KEY:
            return Response({"detail": "AI 검색 서버가 아직 연결되지 않았습니다."}, status=503)

        prompt = (
            "사용자가 MINI 차량 관련 질문을 했습니다. Responses API의 웹 검색으로 실제 검색을 반드시 수행하세요. "
            "검색어에는 site:cafe.naver.com/minilover 를 포함하고 아이러브미니 네이버 카페의 공개 게시글을 우선 확인하세요. "
            "카페 글에서 근거를 찾지 못하면 그 사실을 먼저 밝히고, 근거가 없는 정비 사실을 만들어내지 마세요. "
            "정비 안전과 관련된 답변은 단정하지 말고 전문가 점검이 필요할 수 있음을 안내하세요. "
            "답변은 한국어로 간결하게 쓰고, 검색한 게시글을 인용해 주세요.\n\n질문: " + query
        )
        body = json.dumps({
            "model": settings.OPENAI_SEARCH_MODEL,
            "tools": [{"type": "web_search", "filters": {"allowed_domains": ["cafe.naver.com"]}}],
            "tool_choice": "required",
            "include": ["web_search_call.action.sources"],
            "input": prompt,
        }).encode("utf-8")
        upstream = Request(
            "https://api.openai.com/v1/responses", data=body,
            headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                     "Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        try:
            with urlopen(upstream, timeout=45) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, ValueError):
            return Response({"detail": "카페 검색 답변을 가져오지 못했어요. 잠시 후 다시 시도해 주세요."}, status=502)

        answer = str(payload.get("output_text", "")).strip()
        sources = {}
        for item in payload.get("output", []):
            if item.get("type") == "message":
                for part in item.get("content", []):
                    if part.get("type") == "output_text":
                        answer = answer or str(part.get("text", "")).strip()
                        for annotation in part.get("annotations", []):
                            citation = annotation.get("url_citation", {})
                            url = str(citation.get("url", ""))
                            if url.startswith("https://") and urlparse(url).hostname in {"cafe.naver.com", "m.cafe.naver.com"}:
                                sources[url] = {"title": str(citation.get("title") or "아이러브미니 카페 게시글"), "url": url}
            if item.get("type") == "web_search_call":
                for source in item.get("action", {}).get("sources", []):
                    url = str(source.get("url", ""))
                    if url.startswith("https://") and urlparse(url).hostname in {"cafe.naver.com", "m.cafe.naver.com"}:
                        sources.setdefault(url, {"title": str(source.get("title") or "아이러브미니 카페 게시글"), "url": url})
        if not answer:
            return Response({"detail": "검색 결과에서 답변을 만들지 못했어요. 다른 표현으로 질문해 주세요."}, status=502)
        return Response({"query": query, "answer": answer, "sources": list(sources.values())[:6],
                         "source": "아이러브미니 카페 공개글 웹 검색", "live_search": True})


def _attendance_payload(user, today):
    rows = list(AttendanceCheckin.objects.filter(user=user).order_by("-checkin_date")[:31])
    today_row = next((row for row in rows if row.checkin_date == today), None)
    anchor = today if today_row else today - timedelta(days=1)
    streak = 0
    expected = anchor
    for row in rows:
        if row.checkin_date > expected:
            continue
        if row.checkin_date != expected:
            break
        streak += 1
        expected -= timedelta(days=1)
    balance = AttendanceCheckin.objects.filter(user=user).aggregate(total=Sum("points_awarded"))["total"] or 0
    return {
        "balance_points": balance,
        "checked_in_today": today_row is not None,
        "today_points": today_row.points_awarded if today_row else 0,
        "streak_days": streak,
        "next_bonus_in_days": 7 - (streak % 7) if streak else 7,
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
            yesterday = today - timedelta(days=1)
            previous = AttendanceCheckin.objects.filter(user=request.user, checkin_date=yesterday).first()
            streak = previous.streak_days + 1 if previous else 1
            award = 1000 + (3000 if streak % 7 == 0 else 0)
            AttendanceCheckin.objects.create(user=request.user, checkin_date=today, points_awarded=award, streak_days=streak)
        payload = _attendance_payload(request.user, today)
        payload.update({"earned_points": award, "message": f"출석 완료! {award}P를 적립했어요."})
        return Response(payload, status=status.HTTP_201_CREATED)

class VehicleViewSet(viewsets.ModelViewSet):
    serializer_class = VehicleSerializer
    permission_classes = [permissions.IsAuthenticated, OwnerOrStaff]
    throttle_scope = "vehicle_transfer"
    def get_queryset(self):
        qs = Vehicle.objects.all()
        return qs if self.request.user.is_superuser else qs.filter(
            ownerships__user=self.request.user,
            ownerships__ended_at__isnull=True,
        ).distinct()

    class PassportScanInput(serializers.Serializer):
        vehicle_public_id = serializers.UUIDField()
        plate_number = serializers.CharField(max_length=16)

        def validate_plate_number(self, value):
            try:
                return normalize_plate_number(value)
            except ValueError as exc:
                raise serializers.ValidationError(str(exc)) from exc

    class PlateLookupInput(serializers.Serializer):
        plate_number = serializers.CharField(max_length=16)

        def validate_plate_number(self, value):
            try:
                return normalize_plate_number(value)
            except ValueError as exc:
                raise serializers.ValidationError(str(exc)) from exc

    def _has_plate_check_permission(self, user):
        return PartnerStaff.objects.filter(
            user=user, is_active=True, can_verify_records=True, partner__is_active=True,
        ).exists()

    @action(detail=False, methods=["post"], url_path="lookup-plate", throttle_classes=[ScopedRateThrottle])
    def lookup_plate(self, request):
        data = self.PlateLookupInput(data=request.data)
        data.is_valid(raise_exception=True)
        if not self._has_plate_check_permission(request.user):
            return Response({"detail": "승인된 협력업체 정비이력 권한이 필요합니다."}, status=status.HTTP_403_FORBIDDEN)
        vehicle = Vehicle.objects.filter(
            plate_number=data.validated_data["plate_number"], status="active",
        ).first()
        if vehicle is None:
            return Response({"detail": "등록된 차량 번호를 찾을 수 없습니다. 차주가 차량 번호를 등록했는지 확인해 주세요."}, status=status.HTTP_404_NOT_FOUND)
        return Response({"vehicle": {
            "public_id": str(vehicle.public_id), "plate_number": vehicle.plate_number,
            "model_name": vehicle.model_name, "generation": vehicle.generation,
            "model_year": vehicle.model_year,
        }})

    @action(detail=False, methods=["post"], url_path="scan-passport")
    def scan_passport(self, request):
        data = self.PassportScanInput(data=request.data)
        data.is_valid(raise_exception=True)
        if not self._has_plate_check_permission(request.user):
            return Response({"detail": "승인된 협력업체 정비이력 권한이 필요합니다."}, status=status.HTTP_403_FORBIDDEN)
        vehicle = Vehicle.objects.filter(public_id=data.validated_data["vehicle_public_id"], status="active").first()
        if vehicle is None:
            return Response({"detail": "차량 Passport QR을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
        if not vehicle.plate_number:
            return Response({"detail": "차주가 차량 번호를 등록해야 업체 인증기록을 남길 수 있습니다."}, status=status.HTTP_409_CONFLICT)
        if vehicle.plate_number != data.validated_data["plate_number"]:
            return Response({"detail": "입력한 번호판과 스캔한 QR 차량이 일치하지 않습니다."}, status=status.HTTP_409_CONFLICT)
        history = vehicle.ledger_entries.select_related("partner").order_by("-entry_date", "-id")[:100]
        return Response({
            "plate_confirmed": True,
            "vehicle": {"public_id": str(vehicle.public_id), "model_name": vehicle.model_name,
                        "generation": vehicle.generation, "model_year": vehicle.model_year,
                        "plate_number": vehicle.plate_number,
                        "current_odometer_km": vehicle.current_odometer_km},
            "history": [{"id": row.pk, "date": row.entry_date.isoformat(), "kind": row.kind,
                         "odometer_km": row.odometer_km, "description": row.get_kind_display() if row.created_at < (vehicle.current_ownership.started_at if vehicle.current_ownership else timezone.now()) else row.description,
                         "partner": row.partner.name if row.partner_id else None,
                         "verified": row.source == LedgerEntry.Source.PARTNER}
                        for row in history],
        })
    def perform_create(self, serializer):
        with transaction.atomic():
            relationship = serializer.validated_data.pop("use_relationship", VehicleOwnership.Relationship.OTHER)
            vehicle = serializer.save()
            VehicleOwnership.objects.create(
                vehicle=vehicle,
                user=self.request.user,
                verification_method="account_registration",
                verification_status=VehicleOwnership.VerificationStatus.USER_CLAIMED,
                relationship=relationship,
            )
            if vehicle.plate_number:
                VehiclePlateHistory.objects.create(
                    vehicle=vehicle, plate_number=vehicle.plate_number, changed_by=self.request.user,
                )

    def perform_update(self, serializer):
        with transaction.atomic():
            previous_plate = serializer.instance.plate_number
            relationship = serializer.validated_data.pop("use_relationship", None)
            vehicle = serializer.save()
            if relationship is not None:
                VehicleOwnership.objects.filter(vehicle=vehicle, ended_at__isnull=True).update(relationship=relationship)
            if previous_plate != vehicle.plate_number:
                now = timezone.now()
                VehiclePlateHistory.objects.filter(vehicle=vehicle, ended_at__isnull=True).update(ended_at=now)
                if vehicle.plate_number:
                    VehiclePlateHistory.objects.create(
                        vehicle=vehicle, plate_number=vehicle.plate_number,
                        started_at=now, changed_by=self.request.user,
                    )

    def destroy(self, request, *args, **kwargs):
        vehicle = self.get_object()
        with transaction.atomic():
            locked_vehicle = Vehicle.objects.select_for_update().filter(pk=vehicle.pk).first()
            if locked_vehicle is None:
                return Response({"detail": "차량을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
            if locked_vehicle.ledger_entries.filter(source=LedgerEntry.Source.PARTNER).exists():
                return Response(
                    {"detail": "협력업체 인증기록이 있는 차량은 삭제할 수 없습니다."},
                    status=status.HTTP_409_CONFLICT,
                )
            return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=["get"], url_path="maintenance-summary")
    def maintenance_summary(self, request, pk=None):
        vehicle = self.get_object()
        entries = vehicle.ledger_entries.select_related("partner")
        maintenance = entries.filter(corrections__isnull=True, kind__in=[LedgerEntry.Kind.SERVICE, LedgerEntry.Kind.PART]).order_by("-entry_date", "-id").first()
        pending_qs = vehicle.reminders.filter(completed_at__isnull=True)
        if not request.user.is_superuser:
            pending_qs = pending_qs.filter(created_at__gte=vehicle.current_ownership.started_at)
        pending = list(pending_qs)
        today = timezone.localdate()
        current_km = vehicle.current_odometer_km
        overdue_count = sum(
            1 for row in pending
            if ((row.due_date is not None and row.due_date <= today)
                or (row.due_odometer_km is not None and current_km is not None and row.due_odometer_km <= current_km))
        )
        due_dates = [row.due_date for row in pending if row.due_date is not None]
        due_km = [row.due_odometer_km for row in pending if row.due_odometer_km is not None]
        last_maintenance = LedgerEntrySerializer(maintenance, context=self.get_serializer_context()).data if maintenance else None
        return Response({
            "vehicle_id": vehicle.pk,
            "ledger_count": entries.count(),
            "verified_record_count": entries.filter(source=LedgerEntry.Source.PARTNER).count(),
            "correction_count": entries.filter(corrects__isnull=False).count(),
            "last_maintenance": last_maintenance,
            "pending_reminder_count": len(pending),
            "overdue_reminder_count": overdue_count,
            "next_due_date": min(due_dates).isoformat() if due_dates else None,
            "next_due_odometer_km": min(due_km) if due_km else None,
        })

    class TransferCodeInput(serializers.Serializer):
        code = serializers.CharField(min_length=10, max_length=10, trim_whitespace=True)
        use_relationship = serializers.ChoiceField(choices=VehicleOwnership.Relationship.choices, required=False)

    @action(detail=True, methods=["post"], url_path="transfer-code", throttle_classes=[ScopedRateThrottle])
    def create_transfer_code(self, request, pk=None):
        if request.user.is_staff:
            return Response({"detail": "운영자 계정으로는 차량을 인계할 수 없습니다."}, status=status.HTTP_403_FORBIDDEN)
        vehicle = self.get_object()
        if vehicle.owner_id != request.user.id:
            return Response({"detail": "내 차량만 인계할 수 있습니다."}, status=status.HTTP_403_FORBIDDEN)

        alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        now = timezone.now()
        with transaction.atomic():
            vehicle = Vehicle.objects.select_for_update().get(pk=vehicle.pk)
            if vehicle.owner_id != request.user.id:
                return Response({"detail": "차량 소유자가 변경되었습니다. 다시 확인해 주세요."}, status=status.HTTP_409_CONFLICT)
            VehicleTransferCode.objects.filter(
                vehicle=vehicle, accepted_at__isnull=True, invalidated_at__isnull=True,
            ).update(invalidated_at=now)
            while True:
                code = "".join(secrets.choice(alphabet) for _ in range(10))
                digest = hashlib.sha256(code.encode("ascii")).hexdigest()
                if not VehicleTransferCode.objects.filter(code_digest=digest).exists():
                    break
            transfer = VehicleTransferCode.objects.create(
                vehicle=vehicle,
                previous_owner=request.user,
                code_digest=digest,
                expires_at=now + timedelta(hours=24),
            )

        return Response({
            "code": code,
            "expires_at": transfer.expires_at,
            "model_name": vehicle.model_name,
            "plate_number": vehicle.plate_number,
            "ledger_count": vehicle.ledger_entries.count(),
            "verified_record_count": vehicle.ledger_entries.filter(source=LedgerEntry.Source.PARTNER).count(),
            "correction_count": vehicle.ledger_entries.filter(corrects__isnull=False).count(),
            "reminder_count": vehicle.reminders.count(),
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="cancel-transfer", throttle_classes=[ScopedRateThrottle])
    def cancel_transfer(self, request, pk=None):
        if request.user.is_staff:
            return Response({"detail": "운영자 계정으로는 차량 인계를 취소할 수 없습니다."}, status=status.HTTP_403_FORBIDDEN)
        vehicle = self.get_object()
        if vehicle.owner_id != request.user.id:
            return Response({"detail": "내 차량의 인계만 취소할 수 있습니다."}, status=status.HTTP_403_FORBIDDEN)
        with transaction.atomic():
            vehicle = Vehicle.objects.select_for_update().get(pk=vehicle.pk)
            if vehicle.owner_id != request.user.id:
                return Response({"detail": "차량 소유자가 변경되었습니다. 다시 확인해 주세요."}, status=status.HTTP_409_CONFLICT)
            cancelled = VehicleTransferCode.objects.filter(
                vehicle=vehicle,
                accepted_at__isnull=True,
                invalidated_at__isnull=True,
            ).update(invalidated_at=timezone.now())
        return Response({"cancelled": cancelled})

    def _find_transfer(self, code):
        digest = hashlib.sha256(code.strip().upper().encode("utf-8")).hexdigest()
        transfers = VehicleTransferCode.objects.select_related("vehicle")
        return transfers.filter(
            code_digest=digest,
            accepted_at__isnull=True,
            invalidated_at__isnull=True,
            expires_at__gt=timezone.now(),
        ).first()

    @action(detail=False, methods=["post"], url_path="preview-transfer", throttle_classes=[ScopedRateThrottle])
    def preview_transfer(self, request):
        if request.user.is_staff:
            return Response({"detail": "회원 계정에서 인계 코드를 확인해 주세요."}, status=status.HTTP_403_FORBIDDEN)
        data = self.TransferCodeInput(data=request.data)
        data.is_valid(raise_exception=True)
        transfer = self._find_transfer(data.validated_data["code"])
        if transfer is None or transfer.previous_owner_id == request.user.id or transfer.vehicle.owner_id != transfer.previous_owner_id:
            return Response({"detail": "인계 코드가 틀렸거나 만료·사용되었습니다."}, status=status.HTTP_400_BAD_REQUEST)
        vehicle = transfer.vehicle
        return Response({
            "model_name": vehicle.model_name,
            "plate_number": vehicle.plate_number,
            "generation": vehicle.generation,
            "model_year": vehicle.model_year,
            "current_odometer_km": vehicle.current_odometer_km,
            "ledger_count": vehicle.ledger_entries.count(),
            "verified_record_count": vehicle.ledger_entries.filter(source=LedgerEntry.Source.PARTNER).count(),
            "correction_count": vehicle.ledger_entries.filter(corrects__isnull=False).count(),
            "reminder_count": vehicle.reminders.count(),
            "expires_at": transfer.expires_at,
        })

    @action(detail=False, methods=["post"], url_path="accept-transfer", throttle_classes=[ScopedRateThrottle])
    def accept_transfer(self, request):
        if request.user.is_staff:
            return Response({"detail": "회원 계정에서 차량 인계를 진행해 주세요."}, status=status.HTTP_403_FORBIDDEN)
        data = self.TransferCodeInput(data=request.data)
        data.is_valid(raise_exception=True)
        if "use_relationship" not in data.validated_data:
            return Response({"detail": "인계받을 차량 이용 형태를 선택해 주세요."}, status=status.HTTP_400_BAD_REQUEST)
        now = timezone.now()
        pending = self._find_transfer(data.validated_data["code"])
        if pending is None:
            return Response({"detail": "인계 코드가 틀렸거나 만료·사용되었습니다."}, status=status.HTTP_400_BAD_REQUEST)
        if pending.previous_owner_id == request.user.id:
            return Response({"detail": "판매자와 구매자 계정이 달라야 합니다."}, status=status.HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            vehicle = Vehicle.objects.select_for_update().get(pk=pending.vehicle_id)
            transfer = VehicleTransferCode.objects.select_for_update().filter(
                pk=pending.pk,
                accepted_at__isnull=True,
                invalidated_at__isnull=True,
                expires_at__gt=now,
            ).first()
            if transfer is None:
                return Response({"detail": "인계 코드가 틀렸거나 만료·사용되었습니다."}, status=status.HTTP_400_BAD_REQUEST)
            if transfer.previous_owner_id == request.user.id:
                return Response({"detail": "판매자와 구매자 계정이 달라야 합니다."}, status=status.HTTP_400_BAD_REQUEST)
            if vehicle.pk != transfer.vehicle_id:
                return Response({"detail": "인계 차량 정보가 변경되었습니다."}, status=status.HTTP_409_CONFLICT)
            active_ownership = VehicleOwnership.objects.select_for_update().filter(
                vehicle=vehicle,
                user_id=transfer.previous_owner_id,
                ended_at__isnull=True,
            ).first()
            if active_ownership is None:
                transfer.invalidated_at = now
                transfer.save(update_fields=["invalidated_at"])
                return Response({"detail": "인계 전에 차량 소유자가 변경되었습니다."}, status=status.HTTP_409_CONFLICT)

            active_ownership.ended_at = now
            active_ownership.save(update_fields=["ended_at"])
            VehicleOwnership.objects.create(
                vehicle=vehicle,
                user=request.user,
                started_at=now,
                verification_method="handover_code",
                verification_status=VehicleOwnership.VerificationStatus.USER_CLAIMED,
                relationship=data.validated_data["use_relationship"],
            )
            vehicle.nickname = ""
            vehicle.passport_public = False
            vehicle.save(update_fields=["nickname", "passport_public"])
            transfer.new_owner = request.user
            transfer.accepted_at = now
            transfer.save(update_fields=["new_owner", "accepted_at"])
            VehicleTransferCode.objects.filter(
                vehicle=vehicle, accepted_at__isnull=True, invalidated_at__isnull=True,
            ).exclude(pk=transfer.pk).update(invalidated_at=now)

        return Response({"transferred": True, "vehicle": self.get_serializer(vehicle).data})

class LedgerEntryViewSet(viewsets.ModelViewSet):
    serializer_class = LedgerEntrySerializer
    permission_classes = [permissions.IsAuthenticated, OwnerOrStaff]
    throttle_scope = "verified_record"
    def get_queryset(self):
        qs = LedgerEntry.objects.select_related("vehicle")
        if not self.request.user.is_superuser:
            qs = qs.filter(vehicle__ownerships__user=self.request.user, vehicle__ownerships__ended_at__isnull=True)
        vehicle_id = self.request.query_params.get("vehicle")
        return qs.filter(vehicle_id=vehicle_id) if vehicle_id else qs
    def perform_create(self, serializer):
        entry = serializer.save(source=LedgerEntry.Source.OWNER)
        if entry.odometer_km is not None and (
            entry.vehicle.current_odometer_km is None or entry.odometer_km > entry.vehicle.current_odometer_km
        ):
            entry.vehicle.current_odometer_km = entry.odometer_km
            entry.vehicle.save(update_fields=["current_odometer_km"])

    def update(self, request, *args, **kwargs):
        entry = self.get_object()
        if self.get_serializer().is_inherited(entry):
            return Response({"detail": "인계받은 이전 기록은 변경할 수 없습니다."}, status=status.HTTP_409_CONFLICT)
        if entry.source == LedgerEntry.Source.PARTNER:
            return Response({"detail": "협력업체 인증기록은 수정할 수 없습니다."}, status=status.HTTP_409_CONFLICT)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        entry = self.get_object()
        if self.get_serializer().is_inherited(entry):
            return Response({"detail": "인계받은 이전 기록은 변경할 수 없습니다."}, status=status.HTTP_409_CONFLICT)
        if entry.source == LedgerEntry.Source.PARTNER:
            return Response({"detail": "협력업체 인증기록은 삭제할 수 없습니다."}, status=status.HTTP_409_CONFLICT)
        return super().destroy(request, *args, **kwargs)

    class VerifiedRecordInput(serializers.Serializer):
        vehicle_public_id = serializers.UUIDField()
        plate_number = serializers.CharField(max_length=16)
        partner = serializers.PrimaryKeyRelatedField(queryset=Partner.objects.all())
        kind = serializers.ChoiceField(choices=LedgerEntry.Kind.choices)
        entry_date = serializers.DateField(default=timezone.localdate)
        odometer_km = serializers.IntegerField(min_value=0)
        amount_krw = serializers.IntegerField(min_value=0, default=0)
        description = serializers.CharField(max_length=160)
        quantity_liters = serializers.DecimalField(max_digits=7, decimal_places=2, required=False, allow_null=True)
        part_number = serializers.CharField(max_length=120, required=False, allow_blank=True)
        evidence_url = serializers.URLField(required=False, allow_blank=True)
        corrects = serializers.PrimaryKeyRelatedField(queryset=LedgerEntry.objects.all(), required=False, allow_null=True)
        correction_reason = serializers.CharField(max_length=240, required=False, allow_blank=True)

        def validate_plate_number(self, value):
            try:
                return normalize_plate_number(value)
            except ValueError as exc:
                raise serializers.ValidationError(str(exc)) from exc

        def validate_evidence_url(self, value):
            if value and not value.lower().startswith("https://"):
                raise serializers.ValidationError("증빙 링크는 HTTPS 주소만 등록할 수 있습니다.")
            return value

        def validate(self, attrs):
            if attrs.get("corrects") and not attrs.get("correction_reason", "").strip():
                raise serializers.ValidationError({"correction_reason": "정정 사유를 입력해 주세요."})
            return attrs

    @action(detail=False, methods=["post"], url_path="partner-verified", throttle_classes=[ScopedRateThrottle])
    def create_partner_verified(self, request):
        data = self.VerifiedRecordInput(data=request.data)
        data.is_valid(raise_exception=True)
        partner = data.validated_data["partner"]
        membership = PartnerStaff.objects.filter(
            partner=partner,
            user=request.user,
            is_active=True,
            can_verify_records=True,
            partner__is_active=True,
        ).first()
        if membership is None:
            return Response({"detail": "이 협력업체의 인증기록 발행 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)

        now = timezone.now()
        with transaction.atomic():
            vehicle = Vehicle.objects.select_for_update().filter(
                public_id=data.validated_data["vehicle_public_id"],
                status="active",
            ).first()
            if vehicle is None:
                return Response({"detail": "차량 Passport QR을 확인할 수 없거나 비활성 차량입니다."}, status=status.HTTP_400_BAD_REQUEST)
            current_ownership = vehicle.current_ownership
            if current_ownership is None:
                return Response({"detail": "현재 이용 중인 회원 차량에만 인증기록을 등록할 수 있습니다."}, status=status.HTTP_400_BAD_REQUEST)
            if not vehicle.plate_number or vehicle.plate_number != data.validated_data["plate_number"]:
                return Response({"detail": "확인한 번호판과 QR 차량이 일치하지 않습니다. 다시 대조해 주세요."}, status=status.HTTP_409_CONFLICT)
            correction = data.validated_data.get("corrects")
            duplicate_query = LedgerEntry.objects.filter(
                vehicle=vehicle, kind=data.validated_data["kind"],
                entry_date=data.validated_data["entry_date"], odometer_km=data.validated_data["odometer_km"],
                description__iexact=data.validated_data["description"].strip(), corrects=correction,
            )
            if correction is not None:
                duplicate_query = duplicate_query.filter(partner=partner,
                    amount_krw=data.validated_data["amount_krw"],
                    correction_reason=data.validated_data.get("correction_reason", "").strip())
            duplicate = duplicate_query.first()
            if duplicate is not None:
                return Response({"detail": "같은 차량·날짜·주행거리·작업내용의 기록이 이미 있습니다.",
                                 "duplicate_record_id": duplicate.pk}, status=status.HTTP_409_CONFLICT)
            if correction is not None:
                correction = LedgerEntry.objects.select_for_update().get(pk=correction.pk)
                if correction.corrections.exists():
                    return Response({"detail": "이미 정정된 원본입니다. 가장 최근 정정 기록을 선택해 주세요."}, status=status.HTTP_409_CONFLICT)
                correction.refresh_from_db()
                valid_signature = bool(correction.record_hash) and (
                    ledger_record_hash(correction) == correction.record_hash
                    or (correction.source == LedgerEntry.Source.PARTNER
                        and legacy_ledger_record_hash(correction) == correction.record_hash)
                )
                if (correction.vehicle_id != vehicle.pk
                        or correction.created_at < current_ownership.started_at
                        or correction.source != LedgerEntry.Source.PARTNER
                        or correction.partner_id != partner.pk
                        or not valid_signature):
                    return Response(
                        {"detail": "같은 차량·협력업체의 정상 인증기록만 정정할 수 있습니다."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            entry = LedgerEntry.objects.create(
                vehicle=vehicle,
                kind=data.validated_data["kind"],
                entry_date=data.validated_data["entry_date"],
                odometer_km=data.validated_data["odometer_km"],
                amount_krw=data.validated_data["amount_krw"],
                description=data.validated_data["description"],
                quantity_liters=data.validated_data.get("quantity_liters"),
                source=LedgerEntry.Source.PARTNER,
                partner=partner,
                verified_by=request.user,
                verified_at=now,
                part_number=data.validated_data.get("part_number", ""),
                evidence_url=data.validated_data.get("evidence_url", ""),
                corrects=correction,
                correction_reason=data.validated_data.get("correction_reason", "").strip(),
            )
            entry.record_hash = ledger_record_hash(entry)
            entry.save(update_fields=["record_hash"])
            if correction is not None:
                RecordCorrectionRequest.objects.filter(entry=correction, resolved_at__isnull=True).update(resolved_entry=entry, resolved_at=now)
            if entry.odometer_km is not None and (
                vehicle.current_odometer_km is None or entry.odometer_km > vehicle.current_odometer_km
            ):
                vehicle.current_odometer_km = entry.odometer_km
                vehicle.save(update_fields=["current_odometer_km"])

        return Response(self.get_serializer(entry).data, status=status.HTTP_201_CREATED)

class ReminderViewSet(viewsets.ModelViewSet):
    serializer_class = ReminderSerializer
    permission_classes = [permissions.IsAuthenticated, OwnerOrStaff]
    def get_queryset(self):
        qs = Reminder.objects.select_related("vehicle")
        if not self.request.user.is_superuser:
            qs = qs.filter(vehicle__ownerships__user=self.request.user,
                           vehicle__ownerships__ended_at__isnull=True,
                           created_at__gte=F("vehicle__ownerships__started_at"))
        vehicle_id = self.request.query_params.get("vehicle")
        return qs.filter(vehicle_id=vehicle_id) if vehicle_id else qs
    def perform_update(self, serializer):
        serializer.save(notification_sent_at=None)
    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        reminder = self.get_object()
        reminder.completed_at = timezone.now()
        reminder.save(update_fields=["completed_at"])
        return Response(self.get_serializer(reminder).data)

class PushDeviceView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    class InputSerializer(serializers.Serializer):
        installation_id = serializers.CharField(max_length=128, trim_whitespace=True)
        platform = serializers.ChoiceField(choices=PushDevice.Platform.choices, required=False)

    def post(self, request):
        data = self.InputSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        installation_id = data.validated_data["installation_id"]
        platform = data.validated_data.get("platform")
        device, _ = PushDevice.objects.update_or_create(
            installation_id=installation_id,
            defaults={"user": request.user, "platform": platform or PushDevice.Platform.ANDROID},
        )
        return Response({"registered": True, "platform": device.platform}, status=status.HTTP_200_OK)

    def delete(self, request):
        data = self.InputSerializer(data=request.data, partial=True)
        data.is_valid(raise_exception=True)
        installation_id = data.validated_data.get("installation_id")
        if installation_id:
            PushDevice.objects.filter(user=request.user, installation_id=installation_id).delete()
        else:
            PushDevice.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class NoticeViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NoticeSerializer
    permission_classes = [SafeMethodsOrStaff]
    def get_queryset(self):
        now = timezone.now()
        return Notice.objects.filter(is_published=True, published_at__lte=now).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=now)
        )

class PartnerViewSet(viewsets.ReadOnlyModelViewSet):
    throttle_scope = "partner_review"
    serializer_class = PartnerSerializer
    permission_classes = [SafeMethodsOrStaff]
    queryset = Partner.objects.filter(is_active=True).prefetch_related("introduction_images").annotate(review_count=Count("reviews"), average_rating=Avg("reviews__rating"))

    @action(detail=True, methods=["get"], url_path=r"images/(?P<image_id>[^/.]+)")
    def introduction_image(self, request, pk=None, image_id=None):
        partner = self.get_object()
        image = get_object_or_404(partner.introduction_images, pk=image_id)
        response = HttpResponse(bytes(image.image_data), content_type=image.content_type)
        response["X-Content-Type-Options"] = "nosniff"
        response["Cache-Control"] = "public, max-age=300"
        return response

    def get_permissions(self):
        if getattr(self, "action", None) == "reviews":
            return [permissions.IsAuthenticated()] if self.request.method == "POST" else [permissions.AllowAny()]
        return super().get_permissions()

    @action(detail=True, methods=["get", "post"], url_path="reviews", throttle_classes=[ScopedRateThrottle], throttle_scope="partner_review")
    def reviews(self, request, pk=None):
        partner = self.get_object()
        if request.method == "GET":
            rows = PartnerReview.objects.filter(partner=partner).select_related("user", "user__naver_identity")
            return Response(PartnerReviewSerializer(rows, many=True).data)
        serializer = PartnerReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review, _ = PartnerReview.objects.update_or_create(
            partner=partner, user=request.user,
            defaults={"rating": serializer.validated_data["rating"], "comment": serializer.validated_data.get("comment", "")},
        )
        return Response(PartnerReviewSerializer(review).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"], url_path="service-history", permission_classes=[permissions.AllowAny])
    def service_history(self, request, pk=None):
        partner = self.get_object()
        rows = LedgerEntry.objects.filter(partner=partner, source=LedgerEntry.Source.PARTNER, verified_at__isnull=False)
        grouped = rows.values("kind").annotate(count=Count("id")).order_by("kind")
        return Response({"total": rows.count(), "by_kind": list(grouped)})

    @action(detail=False, methods=["get"], url_path="my-workplaces", permission_classes=[permissions.IsAuthenticated])
    def my_workplaces(self, request):
        memberships = PartnerStaff.objects.filter(
            user=request.user, is_active=True, can_verify_records=True, partner__is_active=True,
        ).select_related("partner")
        return Response([{"id": row.partner_id, "name": row.partner.name} for row in memberships])

class OfferViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OfferSerializer
    permission_classes = [SafeMethodsOrStaff]
    def get_queryset(self):
        now = timezone.now()
        return Offer.objects.filter(is_active=True, partner__is_active=True).filter(
            Q(starts_at__isnull=True) | Q(starts_at__lte=now)
        ).filter(
            Q(ends_at__isnull=True) | Q(ends_at__gte=now)
        )


class PartnerBookingViewSet(viewsets.ModelViewSet):
    serializer_class = PartnerBookingSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "booking"
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        memberships = PartnerStaff.objects.filter(user=self.request.user, is_active=True,
            can_manage_bookings=True, partner__is_active=True).values("partner_id")
        return PartnerBooking.objects.select_related("partner", "vehicle", "customer").filter(
            Q(customer=self.request.user) | Q(partner_id__in=memberships)
        ).distinct()

    def perform_create(self, serializer):
        booking = serializer.save(customer=self.request.user)
        try:
            from .push import send_booking_notification
            send_booking_notification(booking)
        except Exception:
            # Booking persistence must not fail when push delivery is unavailable.
            pass

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel_booking(self, request, pk=None):
        booking = self.get_object()
        if booking.customer_id != request.user.id:
            return Response({"detail": "예약자만 취소할 수 있습니다."}, status=status.HTTP_403_FORBIDDEN)
        if booking.status not in (PartnerBooking.Status.REQUESTED, PartnerBooking.Status.CONFIRMED):
            return Response({"detail": "현재 상태에서는 취소할 수 없습니다."}, status=status.HTTP_409_CONFLICT)
        booking.status = PartnerBooking.Status.CANCELLED
        booking.save(update_fields=["status", "updated_at"])
        try:
            from .push import send_booking_cancel_notification
            send_booking_cancel_notification(booking)
        except Exception:
            pass
        return Response(self.get_serializer(booking).data)

    @action(detail=True, methods=["post"], url_path="respond")
    def respond(self, request, pk=None):
        booking = self.get_object()
        if not PartnerStaff.objects.filter(user=request.user, partner=booking.partner,
                is_active=True, can_manage_bookings=True, partner__is_active=True).exists():
            return Response({"detail": "이 업체의 예약 관리 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)
        outcome = request.data.get("status")
        if booking.status == PartnerBooking.Status.REQUESTED:
            allowed = (PartnerBooking.Status.CONFIRMED, PartnerBooking.Status.REJECTED)
        elif booking.status == PartnerBooking.Status.CONFIRMED:
            allowed = (PartnerBooking.Status.COMPLETED,)
        else:
            return Response({"detail": "이미 종료된 예약입니다."}, status=status.HTTP_409_CONFLICT)
        if outcome not in allowed:
            return Response({"detail": "대기 중인 요청은 확정·거절, 확정된 예약은 완료 처리할 수 있습니다."}, status=status.HTTP_400_BAD_REQUEST)
        note = str(request.data.get("partner_note", "")).strip()
        if len(note) > 500:
            return Response({"detail": "안내 메모는 500자 이내로 입력해 주세요."}, status=status.HTTP_400_BAD_REQUEST)
        booking.status = outcome
        booking.partner_note = note
        booking.save(update_fields=["status", "partner_note", "updated_at"])
        try:
            from .push import send_booking_status_notification
            send_booking_status_notification(booking)
        except Exception:
            pass
        return Response(self.get_serializer(booking).data)
