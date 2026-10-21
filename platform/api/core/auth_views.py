import secrets
import hmac
import json
import urllib.error
import urllib.request
from datetime import timedelta
from urllib.parse import urlencode
import jwt
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.db import models, transaction
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.utils import timezone
from django.views import View
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import ScopedRateThrottle
from .models import (NaverOAuthAttempt, MemberConsent, NaverIdentity, AppleIdentity,
                     Vehicle, VehicleOwnership, VehiclePlateHistory, LedgerEntry,
                     VehicleTransferCode,
                     LedgerEvidence, PointTransaction, RecordCorrectionRequest,
                     PushDevice, AttendanceCheckin, Reminder, PartnerBooking, PartnerReview,
                     MemberPreference, AppReviewAccount, PartnerStaff, Partner)

from .naver_auth import digest, exchange_code, get_profile, jwt_pair, sync_identity, user_for_profile, NaverUnavailable
from .apple_auth import (apple_revocation_configured, verify_apple_identity,
                         revoke_apple_authorization, AppleAuthorizationUnavailable)
from .integrity import ledger_record_hash
from .models import PointRedemptionRequest

class NaverAppRedirect(HttpResponseRedirect):
    allowed_schemes = ["ilovemini"]


class PartnerNaverLoginStartView(View):
    """Start Naver OAuth for an existing, administrator-linked partner employee."""
    def get(self, request):
        if not settings.NAVER_CLIENT_ID or not settings.NAVER_CLIENT_SECRET or not settings.NAVER_REDIRECT_URI:
            messages.error(request, "네이버 로그인 설정을 확인할 수 없습니다. 잠시 후 다시 시도해 주세요.")
            return redirect("partner_admin:login")
        state = secrets.token_urlsafe(32)
        request.session["partner_admin_naver_state"] = state
        query = urlencode({
            "response_type": "code",
            "client_id": settings.NAVER_CLIENT_ID,
            "redirect_uri": settings.NAVER_REDIRECT_URI,
            "state": state,
        })
        return redirect("https://nid.naver.com/oauth2.0/authorize?" + query)


def complete_partner_naver_login(request, state, code):
    expected_state = request.session.pop("partner_admin_naver_state", "")
    if not expected_state or not hmac.compare_digest(expected_state, state or ""):
        messages.error(request, "로그인 요청이 만료되었거나 올바르지 않습니다. 다시 시작해 주세요.")
        return redirect("partner_admin:login")
    if request.GET.get("error") or not code:
        messages.error(request, "네이버 로그인이 취소되었거나 인증에 실패했습니다.")
        return redirect("partner_admin:login")
    try:
        access_token = exchange_code(code, state)
        profile = get_profile(access_token)
    except NaverUnavailable:
        messages.error(request, "네이버 인증 서버에 연결하지 못했습니다. 잠시 후 다시 시도해 주세요.")
        return redirect("partner_admin:login")

    identity = NaverIdentity.objects.select_related("user").filter(
        subject=str(profile.get("id", ""))
    ).first()
    if identity is None:
        messages.error(request, "앱 회원으로 먼저 가입한 뒤 운영자에게 협력업체 담당자 등록을 요청해 주세요.")
        return redirect("partner_admin:login")
    staff = PartnerStaff.objects.filter(
        user=identity.user,
        is_active=True,
        partner__is_active=True,
    ).filter(models.Q(can_manage_bookings=True) | models.Q(can_verify_records=True)).exists()
    if not staff or not identity.user.is_active or identity.user.is_superuser:
        messages.error(request, "활성화된 협력업체 담당자 계정이 아닙니다. 운영자에게 권한을 확인해 주세요.")
        return redirect("partner_admin:login")

    sync_identity(identity, profile)
    login(request, identity.user, backend="django.contrib.auth.backends.ModelBackend")
    return redirect("partner_admin:index")


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
        http_request = getattr(request, "_request", request)
        session = getattr(http_request, "session", None)
        if session and session.get("partner_admin_naver_state"):
            return complete_partner_naver_login(http_request, state, code)
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
            fields = ("id", "name", "email", "nickname", "profile_image", "gender", "birthday", "age", "birthyear", "mobile")
            attempt.profile_data = {key: str(profile[key])[:2048] for key in fields if profile.get(key)}
            attempt.provider_subject = str(profile["id"])[:64]
            attempt.nickname = str(profile.get("nickname", ""))[:80]
            attempt.ticket_digest = digest(ticket)
            attempt.consumed_at = timezone.now()
            attempt.expires_at = timezone.now() + timedelta(minutes=3)
            attempt.save(update_fields=["profile_data", "provider_subject", "nickname", "ticket_digest", "consumed_at", "expires_at"])
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
            profile = dict(attempt.profile_data or {})
            profile["id"] = attempt.provider_subject
            profile.setdefault("nickname", attempt.nickname)
            user = user_for_profile(profile)
            now = timezone.now()
            user.last_login = now
            user.save(update_fields=["last_login"])
            MemberConsent.objects.update_or_create(user=user, defaults={
                "terms_accepted_at": now, "privacy_accepted_at": now,
                "marketing_opt_in": bool(request.data.get("marketing_opt_in", False)),
            })
            attempt.user = user
            attempt.ticket_digest = None
            attempt.profile_data = {}
            attempt.save(update_fields=["user", "ticket_digest", "profile_data"])
            tokens = jwt_pair(user)
        return Response(tokens)


class AppleLoginView(APIView):
    """Verify a native Sign in with Apple identity token and create an app session."""
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "apple_login"
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        token = request.data.get("identity_token", "")
        nonce = request.data.get("nonce", "")
        if request.data.get("terms_accepted") is not True or request.data.get("privacy_accepted") is not True:
            return Response({"detail": "이용약관과 개인정보 처리방침에 동의해야 가입할 수 있습니다."}, status=400)
        if not isinstance(token, str) or not token or not isinstance(nonce, str) or len(nonce) < 16:
            return Response({"detail": "Apple 로그인 정보가 올바르지 않습니다."}, status=400)
        try:
            header = jwt.get_unverified_header(token)
            if header.get("alg") != "RS256" or not header.get("kid"):
                raise jwt.InvalidTokenError("Unexpected signing key")
            with urllib.request.urlopen("https://appleid.apple.com/auth/keys", timeout=6) as response:
                jwks = json.loads(response.read())
            jwk = next((key for key in jwks.get("keys", []) if key.get("kid") == header["kid"]), None)
            if not jwk:
                raise jwt.InvalidTokenError("Unknown signing key")
            public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk))
            claims = jwt.decode(
                token, public_key, algorithms=["RS256"], audience=settings.APPLE_CLIENT_ID,
                issuer="https://appleid.apple.com", options={"require": ["exp", "iat", "sub", "nonce"]},
            )
            if not hmac.compare_digest(str(claims.get("nonce", "")), nonce):
                raise jwt.InvalidTokenError("Nonce mismatch")
        except (jwt.InvalidTokenError, jwt.PyJWKError, ValueError, KeyError, urllib.error.URLError, TimeoutError):
            return Response({"detail": "Apple 로그인을 확인할 수 없습니다. 다시 시도해 주세요."}, status=401)

        subject = str(claims.get("sub", ""))
        email = str(claims.get("email", ""))[:254]
        if not subject:
            return Response({"detail": "Apple 계정 식별값이 없습니다."}, status=401)
        with transaction.atomic():
            identity = AppleIdentity.objects.select_related("user").filter(subject=subject).first()
            if identity is None:
                User = get_user_model()
                username = "apple_" + digest(subject)[:40]
                user = User.objects.filter(username=username).first()
                if user is None:
                    user = User.objects.create_user(username=username, email=email, password=None)
                AppleIdentity.objects.create(user=user, subject=subject, email=email)
            else:
                user = identity.user
                if email and identity.email != email:
                    identity.email = email
                    identity.save(update_fields=["email"])
                if email and not user.email:
                    user.email = email
                    user.save(update_fields=["email"])
            now = timezone.now()
            user.last_login = now
            user.save(update_fields=["last_login"])
            MemberConsent.objects.update_or_create(user=user, defaults={
                "terms_accepted_at": now, "privacy_accepted_at": now,
                "marketing_opt_in": False,
            })
            tokens = jwt_pair(user)
        return Response(tokens)



class AppReviewLoginView(APIView):
    """Authenticate a demo account created by a site administrator for app review."""
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "review_login"
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        username = request.data.get("username", "")
        password = request.data.get("password", "")
        if not isinstance(username, str) or not isinstance(password, str) or not username or not password:
            return Response({"detail": "아이디 또는 비밀번호를 확인해 주세요."}, status=400)

        with transaction.atomic():
            account = AppReviewAccount.objects.select_for_update().filter(
                username=username, is_active=True,
            ).first()
            if not account or not account.password_hash or not check_password(password, account.password_hash):
                return Response({"detail": "아이디 또는 비밀번호를 확인해 주세요."}, status=400)

            User = get_user_model()
            user = account.user
            if user is None:
                if User.objects.filter(username=username).exists():
                    return Response({"detail": "심사용 계정을 사용할 수 없습니다."}, status=503)
                user = User.objects.create_user(
                    username=username, password=None, first_name="앱 심사 데모",
                    is_active=True, is_staff=False, is_superuser=False,
                )
                account.user = user
                account.save(update_fields=["user", "updated_at"])
            if (not user.is_active or user.is_staff or user.is_superuser
                    or NaverIdentity.objects.filter(user=user).exists()
                    or PartnerStaff.objects.filter(user=user, is_active=True, partner__is_active=True).exists()):
                return Response({"detail": "심사용 계정을 사용할 수 없습니다."}, status=503)

            now = timezone.now()
            user.last_login = now
            user.save(update_fields=["last_login"])
            MemberConsent.objects.update_or_create(user=user, defaults={
                "terms_accepted_at": now, "privacy_accepted_at": now,
                "marketing_opt_in": False,
            })
            if not VehicleOwnership.objects.filter(user=user, ended_at__isnull=True).exists():
                vehicle = Vehicle.objects.create(
                    model_name="MINI Cooper S", generation="F56", model_year=2022,
                    manufacturer="MINI", current_odometer_km=46200,
                )
                VehicleOwnership.objects.create(user=user, vehicle=vehicle)
            tokens = jwt_pair(user)
        return Response(tokens)


class AccountDeletionView(APIView):
    """Disable a member login and erase directly identifying account data."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        linked = AppleIdentity.objects.filter(user=request.user).exists()
        return Response({
            "requires_apple_reauthentication": linked,
            "deletion_available": not linked or apple_revocation_configured(),
        })

    def delete(self, request):
        now = timezone.now()
        with transaction.atomic():
            user = get_user_model().objects.select_for_update().get(pk=request.user.pk)
            if not user.is_active:
                return Response({"detail": "이미 삭제된 계정입니다."}, status=401)
            apple = AppleIdentity.objects.filter(user=user).first()
            if apple is not None:
                if not apple_revocation_configured():
                    return Response({"detail": "Apple 계정 연결 해제 설정을 준비 중입니다. 잠시 후 다시 시도해 주세요."}, status=503)
                token = request.data.get("apple_identity_token")
                nonce = request.data.get("apple_nonce")
                code = request.data.get("apple_authorization_code")
                if not all(isinstance(value, str) and value for value in (token, nonce, code)) or len(nonce) < 16:
                    return Response({"detail": "계정 삭제를 위해 Apple 본인 확인이 필요합니다."}, status=400)
                try:
                    claims = verify_apple_identity(token, nonce)
                    if not hmac.compare_digest(str(claims.get("sub", "")), apple.subject):
                        return Response({"detail": "가입한 Apple 계정으로 확인해 주세요."}, status=403)
                    revoke_apple_authorization(code, apple.subject)
                except (jwt.PyJWTError, ValueError, KeyError, urllib.error.URLError, TimeoutError):
                    return Response({"detail": "Apple 본인 확인을 완료하지 못했습니다. 다시 시도해 주세요."}, status=401)
                except AppleAuthorizationUnavailable:
                    return Response({"detail": "Apple 연결 해제를 완료하지 못했습니다. 계정은 삭제되지 않았습니다. 다시 시도해 주세요."}, status=503)
            owned_ids = VehicleOwnership.objects.filter(
                user=user, ended_at__isnull=True,
            ).values("vehicle_id")
            vehicles = list(Vehicle.objects.select_for_update().filter(
                pk__in=owned_ids,
            ))
            RecordCorrectionRequest.objects.filter(requested_by=user).delete()
            for vehicle in vehicles:
                Reminder.objects.filter(vehicle=vehicle).delete()
                entries = vehicle.ledger_entries.all()
                verified_ids = list(entries.filter(
                    source=LedgerEntry.Source.PARTNER,
                ).values_list("pk", flat=True))
                owner_ids = list(entries.filter(
                    source=LedgerEntry.Source.OWNER,
                ).values_list("pk", flat=True))

                retained_owner_ids = set()
                if owner_ids:
                    RecordCorrectionRequest.objects.filter(
                        models.Q(entry_id__in=owner_ids) |
                        models.Q(resolved_entry_id__in=owner_ids)
                    ).delete()
                    retained_owner_ids = set(LedgerEntry.objects.filter(
                        corrects_id__in=owner_ids,
                    ).values_list("corrects_id", flat=True))
                    retained_owner_ids |= set(PointTransaction.objects.filter(
                        ledger_entry_id__in=owner_ids,
                    ).values_list("ledger_entry_id", flat=True))
                    removable_ids = set(owner_ids) - retained_owner_ids
                    if removable_ids:
                        PointTransaction.objects.filter(
                            ledger_entry_id__in=removable_ids,
                        ).update(ledger_entry=None)
                        LedgerEvidence.objects.filter(entry_id__in=removable_ids).delete()
                        LedgerEntry.objects.filter(pk__in=removable_ids).update(corrects=None)
                        LedgerEntry.objects.filter(pk__in=removable_ids).delete()

                VehicleOwnership.objects.filter(vehicle=vehicle, user=user).update(
                    user=None, ended_at=now,
                )
                VehicleTransferCode.objects.filter(
                    vehicle=vehicle, accepted_at__isnull=True, invalidated_at__isnull=True,
                ).update(invalidated_at=now)
                VehiclePlateHistory.objects.filter(vehicle=vehicle).delete()
                if verified_ids or retained_owner_ids:
                    # Certified maintenance is kept for the disclosed one-year
                    # period, detached from the member and vehicle identifiers.
                    LedgerEvidence.objects.filter(entry__vehicle=vehicle).delete()
                    for entry in vehicle.ledger_entries.all():
                        entry.evidence_url = ""
                        entry.description = entry.get_kind_display()
                        entry.line_items = []
                        entry.part_number = ""
                        entry.correction_reason = ""
                        if entry.source == LedgerEntry.Source.PARTNER or entry.record_hash:
                            entry.record_hash = ledger_record_hash(entry)
                        entry.save(update_fields=["evidence_url", "description", "line_items",
                                                  "part_number", "correction_reason", "record_hash"])
                    vehicle.plate_number = ""
                    vehicle.vin_hash = ""
                    vehicle.nickname = ""
                    vehicle.passport_public = False
                    vehicle.retention_expires_at = now + timedelta(days=365)
                    vehicle.save(update_fields=[
                        "plate_number", "vin_hash", "nickname", "passport_public",
                        "retention_expires_at",
                    ])
                else:
                    vehicle.delete()

            # Remove the departed member's identity from older ownership rows,
            # while leaving any current owner's vehicle details untouched.
            VehicleOwnership.objects.filter(user=user).update(user=None)
            PointRedemptionRequest.objects.filter(
                member=user, status__in=[PointRedemptionRequest.Status.PENDING,
                                        PointRedemptionRequest.Status.APPROVED],
            ).update(status=PointRedemptionRequest.Status.CANCELLED, responded_at=now)

            PushDevice.objects.filter(user=user).delete()
            AttendanceCheckin.objects.filter(user=user).delete()
            PartnerBooking.objects.filter(customer=user).delete()
            PartnerReview.objects.filter(user=user).delete()
            PartnerStaff.objects.filter(user=user).delete()
            MemberPreference.objects.filter(user=user).delete()
            NaverOAuthAttempt.objects.filter(user=user).delete()
            MemberConsent.objects.filter(user=user).delete()
            NaverIdentity.objects.filter(user=user).delete()
            AppleIdentity.objects.filter(user=user).delete()
            AppReviewAccount.objects.filter(user=user).update(user=None)

            # Keep an unidentifiable inactive tombstone only for protected point
            # and verified-history audit references.
            user.username = f"deleted_{secrets.token_hex(16)}"
            user.email = ""
            user.first_name = ""
            user.last_name = ""
            user.last_login = None
            user.is_active = False
            user.set_unusable_password()
            user.save(update_fields=[
                "username", "email", "first_name", "last_name",
                "last_login", "is_active", "password",
            ])
        return Response(status=status.HTTP_204_NO_CONTENT)
