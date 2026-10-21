import json
from unittest.mock import patch
from urllib.parse import parse_qs

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from django.test import SimpleTestCase, override_settings

from .apple_auth import AppleAuthorizationUnavailable, revoke_apple_authorization


class Response:
    status = 200

    def __init__(self, data):
        self.data = data

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return json.dumps(self.data).encode()


class AppleRevocationTests(SimpleTestCase):
    def setUp(self):
        self.key = ec.generate_private_key(ec.SECP256R1())
        pem = self.key.private_bytes(serialization.Encoding.PEM,
                                     serialization.PrivateFormat.PKCS8,
                                     serialization.NoEncryption()).decode()
        self.config = override_settings(APPLE_TEAM_ID="test-team", APPLE_KEY_ID="test-key",
                                        APPLE_PRIVATE_KEY=pem)
        self.config.enable()
        self.addCleanup(self.config.disable)

    @patch("core.apple_auth.verify_apple_identity", return_value={"sub": "member-subject"})
    @patch("core.apple_auth.urllib.request.urlopen")
    def test_exchanges_code_and_revokes_only_its_bound_refresh_token(self, urlopen, _verify):
        urlopen.side_effect = [
            Response({"id_token": "signed-id-token", "refresh_token": "apple-refresh-token"}),
            Response({}),
        ]
        revoke_apple_authorization("one-time-code", "member-subject")
        exchange = urlopen.call_args_list[0].args[0]
        revoke = urlopen.call_args_list[1].args[0]
        exchange_body = parse_qs(exchange.data.decode())
        revoke_body = parse_qs(revoke.data.decode())
        claims = jwt.decode(exchange_body["client_secret"][0], self.key.public_key(),
                            algorithms=["ES256"], audience="https://appleid.apple.com")
        self.assertEqual(claims["iss"], "test-team")
        self.assertEqual(exchange_body["code"], ["one-time-code"])
        self.assertEqual(revoke.full_url, "https://appleid.apple.com/auth/revoke")
        self.assertEqual(revoke_body["token"], ["apple-refresh-token"])
        self.assertEqual(revoke_body["token_type_hint"], ["refresh_token"])

    @patch("core.apple_auth.verify_apple_identity", return_value={"sub": "someone-else"})
    @patch("core.apple_auth.urllib.request.urlopen")
    def test_does_not_revoke_an_authorization_code_from_another_member(self, urlopen, _verify):
        urlopen.return_value = Response({"id_token": "signed-id-token", "refresh_token": "token"})
        with self.assertRaises(AppleAuthorizationUnavailable):
            revoke_apple_authorization("wrong-code", "member-subject")
        self.assertEqual(urlopen.call_count, 1)
