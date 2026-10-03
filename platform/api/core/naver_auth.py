import hashlib
import json
import secrets
import urllib.error
import urllib.parse
import urllib.request
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from .models import NaverIdentity
from .member_display import sync_profile_email

class NaverUnavailable(Exception):
    pass


def digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def exchange_code(code, state):
    params = urllib.parse.urlencode({
        "grant_type": "authorization_code", "client_id": settings.NAVER_CLIENT_ID,
        "client_secret": settings.NAVER_CLIENT_SECRET, "code": code, "state": state,
    })
    request = urllib.request.Request("https://nid.naver.com/oauth2.0/token?" + params)
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            data = json.loads(response.read())
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        raise NaverUnavailable from exc
    if data.get("error") or not data.get("access_token"):
        raise NaverUnavailable
    return data["access_token"]


def get_profile(access_token):
    request = urllib.request.Request(
        "https://openapi.naver.com/v1/nid/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            data = json.loads(response.read())
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        raise NaverUnavailable from exc
    profile = data.get("response") or {}
    if data.get("resultcode") != "00" or not profile.get("id"):
        raise NaverUnavailable
    return profile


def user_for_profile(profile):
    User = get_user_model()
    subject = str(profile["id"])
    try:
        with transaction.atomic():
            identity = NaverIdentity.objects.select_related("user").filter(subject=subject).first()
            if identity:
                if profile.get("nickname"):
                    identity.nickname = str(profile["nickname"])[:80]
                    identity.save(update_fields=["nickname"])
                sync_profile_email(identity.user, profile)
                return identity.user
            username = "naver_" + digest(subject)[:40]
            user = User.objects.create_user(username=username, password=None)
            sync_profile_email(user, profile)
            user.set_unusable_password()
            user.save(update_fields=["password"])
            NaverIdentity.objects.create(user=user, subject=subject, nickname=str(profile.get("nickname", ""))[:80])
            return user
    except IntegrityError:
        return NaverIdentity.objects.select_related("user").get(subject=subject).user


def jwt_pair(user):
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}
