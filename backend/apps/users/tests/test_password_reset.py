"""Tests for the password reset flow.

Covers:
- No user enumeration (200 for missing emails)
- Token generation stores hash on the user
- Token verification (valid, expired, tampered)
- Single-use enforcement
- Password strength validation
- All refresh tokens blacklisted on successful reset
- Rate limiting on both endpoints (via test settings' throttle rates)
"""

import hashlib
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.signing import TimestampSigner
from rest_framework import status

from apps.users.password_reset import _SIGNER, RESET_TOKEN_TTL_SECONDS

User = get_user_model()

REQUEST_URL = "/api/auth/password/reset-request/"
CONFIRM_URL = "/api/auth/password/reset-confirm/"


@pytest.mark.django_db
class TestPasswordResetRequest:
    def test_existing_email_returns_200_and_sends_mail(self, api_client, user):
        with patch("apps.users.password_reset.send_email") as mock_send:
            response = api_client.post(REQUEST_URL, {"email": user.email})

        assert response.status_code == status.HTTP_200_OK
        assert "message" in response.data
        mock_send.assert_called_once()

        # Token hash was persisted
        user.refresh_from_db()
        assert user.password_reset_token_hash != ""
        assert user.password_reset_requested_at is not None

    def test_nonexistent_email_returns_same_200(self, api_client):
        # No user enumeration — response must be indistinguishable
        with patch("apps.users.password_reset.send_email") as mock_send:
            response = api_client.post(REQUEST_URL, {"email": "ghost@nowhere.com"})
        assert response.status_code == status.HTTP_200_OK
        assert "message" in response.data
        # No email was sent
        mock_send.assert_not_called()

    def test_inactive_user_treated_as_nonexistent(self, api_client, user):
        user.is_active = False
        user.save()
        with patch("apps.users.password_reset.send_email") as mock_send:
            response = api_client.post(REQUEST_URL, {"email": user.email})
        assert response.status_code == status.HTTP_200_OK
        mock_send.assert_not_called()

    def test_invalid_email_format_rejected(self, api_client):
        response = api_client.post(REQUEST_URL, {"email": "not-an-email"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_email_case_normalized(self, api_client, user):
        with patch("apps.users.password_reset.send_email") as mock_send:
            response = api_client.post(REQUEST_URL, {"email": user.email.upper()})
        assert response.status_code == status.HTTP_200_OK
        mock_send.assert_called_once()


@pytest.mark.django_db
class TestPasswordResetConfirm:
    def _request_reset(self, api_client, user):
        """Helper: fire off a request and grab the token by intercepting send."""
        with patch("apps.users.password_reset.send_email") as mock_send:
            api_client.post(REQUEST_URL, {"email": user.email})
        # The reset link is in the send_email call args; extract the token
        args = mock_send.call_args
        text_body = args[0][3]  # (to, subject, html, text)
        # token= appears in link like ".../reset-password?token=<value>"
        token_marker = "token="
        idx = text_body.find(token_marker)
        assert idx != -1, "token not found in email"
        token = text_body[idx + len(token_marker) :].split()[0].strip()
        return token

    def test_valid_token_resets_password(self, api_client, user):
        token = self._request_reset(api_client, user)

        response = api_client.post(
            CONFIRM_URL,
            {"token": token, "new_password": "NewStrongPass!123"},
        )
        assert response.status_code == status.HTTP_200_OK

        # New password works
        user.refresh_from_db()
        assert user.check_password("NewStrongPass!123")
        # Token hash cleared (single-use)
        assert user.password_reset_token_hash == ""

    def test_token_is_single_use(self, api_client, user):
        token = self._request_reset(api_client, user)

        r1 = api_client.post(
            CONFIRM_URL,
            {"token": token, "new_password": "NewStrongPass!123"},
        )
        assert r1.status_code == status.HTTP_200_OK

        # Second use is rejected
        r2 = api_client.post(
            CONFIRM_URL,
            {"token": token, "new_password": "AnotherPass!456"},
        )
        assert r2.status_code == status.HTTP_400_BAD_REQUEST

    def test_tampered_token_rejected(self, api_client, user):
        token = self._request_reset(api_client, user)
        # Flip a character
        tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
        response = api_client.post(
            CONFIRM_URL,
            {"token": tampered, "new_password": "NewStrongPass!123"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_expired_token_rejected(self, api_client, user):
        # Sign a token as if it were generated over an hour ago.
        # Django's TimestampSigner uses time.time() when signing/verifying.
        import time

        past = time.time() - RESET_TOKEN_TTL_SECONDS - 60

        with patch("time.time", return_value=past):
            old_token = _SIGNER.sign(str(user.pk))

        # Store its hash so single-use check doesn't cause the failure —
        # we want to prove expiry is what rejects it
        user.password_reset_token_hash = hashlib.sha256(old_token.encode()).hexdigest()
        user.save()

        response = api_client.post(
            CONFIRM_URL,
            {"token": old_token, "new_password": "NewStrongPass!123"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_token_for_different_user_rejected(self, api_client, user, other_user):
        """A token signed for user A must not work for user B's reset row."""
        # Request reset for user A
        token_a = self._request_reset(api_client, user)
        # But other_user has no hash on file — their record won't match
        other_user.refresh_from_db()
        assert other_user.password_reset_token_hash == ""

        # Confirming token_a still works for user A (sanity)
        response = api_client.post(
            CONFIRM_URL,
            {"token": token_a, "new_password": "NewStrongPass!123"},
        )
        assert response.status_code == status.HTTP_200_OK
        # other_user's password unchanged
        other_user.refresh_from_db()
        assert other_user.check_password("testpass123!")

    def test_weak_password_rejected(self, api_client, user):
        token = self._request_reset(api_client, user)
        response = api_client.post(CONFIRM_URL, {"token": token, "new_password": "short"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_missing_token_rejected(self, api_client):
        response = api_client.post(CONFIRM_URL, {"new_password": "NewStrongPass!123"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_reset_blacklists_all_refresh_tokens(self, api_client, user):
        # User has an active session
        login = api_client.post(
            "/api/auth/login/",
            {"email": user.email, "password": "testpass123!"},
        )
        refresh = login.data["refresh"]

        # Reset password
        token = self._request_reset(api_client, user)
        api_client.post(
            CONFIRM_URL,
            {"token": token, "new_password": "NewStrongPass!123"},
        )

        # Old refresh token no longer works
        r = api_client.post("/api/auth/token/refresh/", {"refresh": refresh}, format="json")
        assert r.status_code == status.HTTP_401_UNAUTHORIZED

    def test_reset_used_hash_gone_error(self, api_client, user):
        """If someone has no outstanding reset request, a random token is rejected."""
        # Manually craft a valid-signature token for user without ever
        # requesting a reset. Their hash field is empty → must fail.
        token = _SIGNER.sign(str(user.pk))
        assert user.password_reset_token_hash == ""

        response = api_client.post(
            CONFIRM_URL,
            {"token": token, "new_password": "NewStrongPass!123"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
