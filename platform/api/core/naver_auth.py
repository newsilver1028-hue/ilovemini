import logging
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
    logging.getLogger(__name__).warning(
        "NAVER_RAW_PROFILE name_key=%s email_key=%s name_value=%s email_value=%s",
        "name" in profile, "email" in profile, bool(profile.get("name")), bool(profile.get("email")),
    )
    return profile


def sync_identity(identity, profile):
    changed = []
    for field in ("name", "email", "nickname", "profile_image", "gender", "birthday", "age", "birthyear", "mobile"):
        value = str(profile.get(field) or "").strip()
        limit = identity._meta.get_field(field).max_length
        value = value[:limit] if limit else value
        if value and getattr(identity, field) != value:
            setattr(identity, field, value)
            changed.append(field)
    if changed:
        identity.save(update_fields=changed)
    sync_profile_email(identity.user, profile)


def user_for_profile(profile):
    User = get_user_model()
    subject = str(profile["id"])
    try:
        with transaction.atomic():
            identity = NaverIdentity.objects.select_related("user").filter(subject=subject).first()
            if identity is None:
                user = User.objects.create_user(username="naver_" + digest(subject)[:40], password=None)
                identity = NaverIdentity.objects.create(user=user, subject=subject)
            sync_identity(identity, profile)
            return identity.user
    except IntegrityError:
        identity = NaverIdentity.objects.select_related("user").get(subject=subject)
        sync_identity(identity, profile)
        return identity.user


def jwt_pair(user):
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}
