import secrets
from datetime import timedelta
from urllib.parse import urlencode
from django.conf import settings
from django.db import transaction
from django.http import HttpResponseRedirect
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import ScopedRateThrottle
from .models import NaverOAuthAttempt, MemberConsent
from .naver_auth import digest, exchange_code, get_profile, jwt_pair, user_for_profile, NaverUnavailable

class NaverAppRedirect(HttpResponseRedirect):
    allowed_schemes = ["ilovemini"]

class NaverStartView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "naver_start"
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    def post(self, request):
        if not settings.NAVER_CLIENT_ID or not settings.NAVER_CLIENT_SECRET or not settings.NAVER_REDIRECT_URI:
            return Response({"detail": "네이버 로그인 설정이 아직 완료되지 않았습니다."}, status=503)
        state = secrets.token_urlsafe(32)
        NaverOAuthAttempt.objects.create(state_digest=digest(state), expires_at=timezone.now() + timedelta(minutes=10))
        query = urlencode({"response_type": "code", "client_id": settings.NAVER_CLIENT_ID,
                          "redirect_uri": settings.NAVER_REDIRECT_URI, "state": state})
        return Response({"authorization_url": "https://nid.naver.com/oauth2.0/authorize?" + query})

class NaverCallbackView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    def get(self, request):
        state = request.query_params.get("state", "")
        code = request.query_params.get("code", "")
        if request.query_params.get("error") or not state or not code:
            return Response({"detail": "네이버 로그인이 취소되었거나 인증에 실패했습니다."}, status=400)
        attempt = NaverOAuthAttempt.objects.filter(state_digest=digest(state), consumed_at__isnull=True,
                                                    expires_at__gt=timezone.now()).first()
        if not attempt:
            return Response({"detail": "만료되었거나 올바르지 않은 로그인 요청입니다."}, status=400)
        try:
            access_token = exchange_code(code, state)
            profile = get_profile(access_token)
            if not profile.get("id"):
                return Response({"detail": "네이버 회원 정보를 확인할 수 없습니다."}, status=502)
        except NaverUnavailable:
            return Response({"detail": "네이버 인증 서버에 연결하지 못했습니다."}, status=502)
        ticket = secrets.token_urlsafe(32)
        with transaction.atomic():
            attempt = NaverOAuthAttempt.objects.select_for_update().get(pk=attempt.pk)
            if attempt.consumed_at or attempt.expires_at <= timezone.now():
                return Response({"detail": "로그인 요청이 이미 사용되었거나 만료되었습니다."}, status=400)
            attempt.provider_subject = str(profile["id"])[:64]
            attempt.nickname = str(profile.get("nickname", ""))[:80]
            attempt.ticket_digest = digest(ticket)
            attempt.consumed_at = timezone.now()
            attempt.expires_at = timezone.now() + timedelta(minutes=3)
            attempt.save(update_fields=["provider_subject", "nickname", "ticket_digest", "consumed_at", "expires_at"])
        return NaverAppRedirect(settings.MOBILE_AUTH_REDIRECT_URI + "?" + urlencode({"ticket": ticket}))

class NaverCompleteView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "naver_complete"
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    def post(self, request):
        ticket = request.data.get("ticket", "")
        if request.data.get("terms_accepted") is not True or request.data.get("privacy_accepted") is not True:
            return Response({"detail": "이용약관과 개인정보 처리 안내에 동의해야 가입할 수 있습니다."}, status=400)
        if not isinstance(ticket, str) or len(ticket) < 24:
            return Response({"detail": "로그인 확인값이 올바르지 않습니다."}, status=400)
        with transaction.atomic():
            attempt = NaverOAuthAttempt.objects.select_for_update().filter(
                ticket_digest=digest(ticket), consumed_at__isnull=False,
                expires_at__gt=timezone.now(), provider_subject__gt="",
            ).first()
            if not attempt:
                return Response({"detail": "로그인 확인값이 만료되었거나 이미 사용되었습니다."}, status=400)
            user = user_for_profile({"id": attempt.provider_subject, "nickname": attempt.nickname})
            now = timezone.now()
            MemberConsent.objects.update_or_create(user=user, defaults={
                "terms_accepted_at": now, "privacy_accepted_at": now,
                "marketing_opt_in": bool(request.data.get("marketing_opt_in", False)),
            })
            attempt.user = user
            attempt.ticket_digest = None
            attempt.save(update_fields=["user", "ticket_digest"])
            tokens = jwt_pair(user)
        return Response(tokens)
