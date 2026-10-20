import json
import time
from unittest.mock import patch

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from django.conf import settings
from django.test import TestCase
from rest_framework.test import APIClient

from .models import AppleIdentity, MemberConsent


class _JwksResponse:
    def __init__(self, data):
        self.data = json.dumps(data).encode()

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self.data


class AppleLoginTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.public_jwk = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(self.private_key.public_key()))
        self.public_jwk.update({"kid": "apple-test-key", "alg": "RS256", "use": "sig"})

    def token(self, *, sub="apple-subject", nonce="a" * 32):
        now = int(time.time())
        return jwt.encode(
            {
                "iss": "https://appleid.apple.com",
                "aud": settings.APPLE_CLIENT_ID,
                "sub": sub,
                "email": "private@example.com",
                "nonce": nonce,
                "iat": now,
                "exp": now + 300,
            },
            self.private_key,
            algorithm="RS256",
            headers={"kid": "apple-test-key"},
        )

    def test_requires_terms_and_privacy_consent(self):
        response = self.client.post("/api/auth/apple/", {"identity_token": "bad", "nonce": "a" * 32}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(AppleIdentity.objects.count(), 0)

    @patch("core.auth_views.urllib.request.urlopen")
    def test_verifies_apple_token_and_creates_session(self, urlopen):
        urlopen.return_value = _JwksResponse({"keys": [self.public_jwk]})
        response = self.client.post(
            "/api/auth/apple/",
            {"identity_token": self.token(), "nonce": "a" * 32, "terms_accepted": True, "privacy_accepted": True},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertIn("access", response.data)
        self.assertEqual(AppleIdentity.objects.count(), 1)
        self.assertTrue(MemberConsent.objects.filter(user__apple_identity__subject="apple-subject").exists())

    @patch("core.auth_views.urllib.request.urlopen")
    def test_rejects_nonce_mismatch(self, urlopen):
        urlopen.return_value = _JwksResponse({"keys": [self.public_jwk]})
        response = self.client.post(
            "/api/auth/apple/",
            {"identity_token": self.token(nonce="b" * 32), "nonce": "a" * 32, "terms_accepted": True, "privacy_accepted": True},
            format="json",
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(AppleIdentity.objects.count(), 0)
