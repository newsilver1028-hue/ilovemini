"""Native Apple reauthentication and authorization revocation.

Authorization codes and tokens are used transiently and never stored or logged.
"""
import hmac
import json
import time
import urllib.error
import urllib.request
from urllib.parse import urlencode

import jwt
from django.conf import settings


class AppleAuthorizationUnavailable(Exception):
    pass


def apple_revocation_configured():
    return bool(settings.APPLE_TEAM_ID and settings.APPLE_KEY_ID and settings.APPLE_PRIVATE_KEY)


def verify_apple_identity(token, nonce=None):
    header = jwt.get_unverified_header(token)
    if header.get("alg") != "RS256" or not header.get("kid"):
        raise jwt.InvalidTokenError("Unexpected signing key")
    with urllib.request.urlopen("https://appleid.apple.com/auth/keys", timeout=8) as response:
        keys = json.loads(response.read()).get("keys", [])
    key = next((key for key in keys if key.get("kid") == header["kid"]), None)
    if key is None:
        raise jwt.InvalidTokenError("Unknown signing key")
    claims = jwt.decode(
        token, jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key)),
        algorithms=["RS256"], audience=settings.APPLE_CLIENT_ID,
        issuer="https://appleid.apple.com", options={"require": ["exp", "iat", "sub"]},
    )
    if nonce is not None and not hmac.compare_digest(str(claims.get("nonce", "")), nonce):
        raise jwt.InvalidTokenError("Nonce mismatch")
    return claims


def revoke_apple_authorization(code, expected_subject):
    if not apple_revocation_configured():
        raise AppleAuthorizationUnavailable
    try:
        issued = int(time.time())
        secret = jwt.encode(
            {"iss": settings.APPLE_TEAM_ID, "iat": issued, "exp": issued + 300,
             "aud": "https://appleid.apple.com", "sub": settings.APPLE_CLIENT_ID},
            settings.APPLE_PRIVATE_KEY, algorithm="ES256", headers={"kid": settings.APPLE_KEY_ID},
        )
        base = {"client_id": settings.APPLE_CLIENT_ID, "client_secret": secret}
        request = urllib.request.Request(
            "https://appleid.apple.com/auth/token",
            data=urlencode({**base, "code": code, "grant_type": "authorization_code"}).encode(),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            tokens = json.loads(response.read())
        # Bind the exchanged code to this member, not just the submitted token.
        claims = verify_apple_identity(tokens["id_token"])
        if not hmac.compare_digest(str(claims["sub"]), expected_subject):
            raise AppleAuthorizationUnavailable
        token = tokens.get("refresh_token") or tokens.get("access_token")
        if not isinstance(token, str) or not token:
            raise AppleAuthorizationUnavailable
        token_type = "refresh_token" if tokens.get("refresh_token") else "access_token"
        request = urllib.request.Request(
            "https://appleid.apple.com/auth/revoke",
            data=urlencode({**base, "token": token, "token_type_hint": token_type}).encode(),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            if response.status != 200:
                raise AppleAuthorizationUnavailable
    except (jwt.PyJWTError, ValueError, KeyError, TypeError, urllib.error.URLError, TimeoutError) as exc:
        raise AppleAuthorizationUnavailable from exc
