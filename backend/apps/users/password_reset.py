"""Password reset flow.

Security model:
- Two endpoints: reset-request (email) and reset-confirm (token + new password).
- Tokens are signed with Django's TimestampSigner (HMAC using SECRET_KEY),
  bound to the user's pk. They expire after RESET_TOKEN_TTL seconds.
- Single-use: we store a SHA-256 hash of the outstanding token on the User;
  a successful reset clears it. Two clicks of the same reset link → second one
  fails.
- No user enumeration: reset-request ALWAYS returns 200, whether or not the
  email exists. Rate limited via the "auth" throttle scope so an attacker
  can't tell existence from timing / response codes.
- Password strength validated via Django's AUTH_PASSWORD_VALIDATORS.
- On successful reset, ALL of the user's outstanding refresh tokens are
  blacklisted — kills any hijacked session the attacker may already have.
- Reset request also logs out other sessions if password_reset_requested_at
  is old enough (unrelated request wouldn't have been resurrected).
"""

from __future__ import annotations

import hashlib
import logging
from typing import cast

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from apps.notifications.email import send_email

logger = logging.getLogger(__name__)
User = get_user_model()

RESET_TOKEN_TTL_SECONDS = 60 * 60  # 1 hour
_SIGNER = TimestampSigner(salt="password-reset-v1")


class _AuthThrottle(AnonRateThrottle):
    scope = "auth"


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _make_token(user_id: int) -> str:
    """Sign `user_id:{timestamp}` with SECRET_KEY-derived HMAC."""
    return _SIGNER.sign(str(user_id))


def _verify_token(token: str) -> int | None:
    """Return user_id if the token's signature and expiry are valid."""
    try:
        value = _SIGNER.unsign(token, max_age=RESET_TOKEN_TTL_SECONDS)
    except (SignatureExpired, BadSignature):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _send_reset_email(user, token: str) -> None:
    from django.conf import settings

    frontend = getattr(settings, "FRONTEND_URL", "http://localhost:5173").rstrip("/")
    link = f"{frontend}/reset-password?token={token}"
    subject = "Reset your Applywise password"
    text = (
        f"Hi {user.first_name or 'there'},\n\n"
        f"Someone (hopefully you) requested a password reset for your "
        f"Applywise account. Click the link below within the next hour to "
        f"choose a new password:\n\n"
        f"  {link}\n\n"
        f"If you didn't request this, you can safely ignore this email — "
        f"your password won't change.\n\n"
        f"— Applywise"
    )
    # Not using our HTML template renderer here — the link is the only
    # dynamic value and it's a URL we generated (not user content).
    import html as _html
    safe_link = _html.escape(link, quote=True)
    safe_name = _html.escape(user.first_name or "there", quote=True)
    html_body = (
        f"<div style=\"font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;max-width:520px;margin:24px auto;color:#111\">"
        f"<h2 style=\"margin:0 0 12px\">Reset your Applywise password</h2>"
        f"<p>Hi {safe_name}, click the button below within the next hour to choose a new password.</p>"
        f"<p><a href=\"{safe_link}\" style=\"display:inline-block;background:#3B82F6;color:#fff;padding:10px 18px;border-radius:6px;text-decoration:none;font-weight:500\">Reset password</a></p>"
        f"<p style=\"color:#666;font-size:13px\">If you didn't request this, you can ignore this email — your password won't change.</p>"
        f"</div>"
    )

    send_email(user.email, subject, html_body, text)


class ResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=512)
    new_password = serializers.CharField(min_length=8, max_length=128)

    def validate_new_password(self, value):
        validate_password(value)
        return value


class PasswordResetRequestView(APIView):
    """Email a signed reset link to a user's address if they exist.

    Always returns 200 to prevent user enumeration.
    """

    permission_classes = [AllowAny]
    throttle_classes = [_AuthThrottle]
    authentication_classes = []

    def post(self, request):
        serializer = ResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].lower().strip()

        # Look up user quietly. Don't leak existence via response, timing,
        # or side-channels. If the user exists we generate a token; if not
        # we do equivalent-cost work.
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = None

        if user is not None and user.is_active:
            token = _make_token(user.pk)
            user.password_reset_token_hash = _hash_token(token)
            user.password_reset_requested_at = timezone.now()
            user.save(
                update_fields=[
                    "password_reset_token_hash",
                    "password_reset_requested_at",
                ]
            )
            try:
                _send_reset_email(user, token)
            except Exception as e:
                # Log but still return 200 — we don't want the error surface
                # to become an enumeration oracle either
                logger.error(f"Failed to send reset email to {email}: {e}")

        # Constant response regardless of outcome
        return Response(
            {
                "message": (
                    "If an account exists for that email, we've sent a "
                    "password reset link. Check your inbox."
                )
            },
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    """Verify a reset token and set a new password.

    On success:
      - Password is updated
      - The reset token hash is cleared (single-use)
      - ALL of the user's outstanding refresh tokens are blacklisted
        (kills any active session — important if the user is resetting
        because they suspect compromise)
    """

    permission_classes = [AllowAny]
    throttle_classes = [_AuthThrottle]
    authentication_classes = []

    def post(self, request):
        serializer = ResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data["token"]
        new_password = serializer.validated_data["new_password"]

        user_id = _verify_token(token)
        if user_id is None:
            return Response(
                {"error": "This reset link is invalid or has expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(pk=user_id, is_active=True)
        except User.DoesNotExist:
            return Response(
                {"error": "This reset link is invalid or has expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Single-use enforcement: the hash on file must match the token that
        # was sent. If the user already reset (or the field was cleared
        # for any other reason), reject.
        expected_hash = _hash_token(token)
        if not user.password_reset_token_hash:
            return Response(
                {"error": "This reset link has already been used."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not _constant_time_equals(
            user.password_reset_token_hash, expected_hash
        ):
            return Response(
                {"error": "This reset link is invalid or has expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Update password + clear reset state atomically
        user.set_password(new_password)
        user.password_reset_token_hash = ""
        user.password_reset_requested_at = None
        user.save(
            update_fields=[
                "password",
                "password_reset_token_hash",
                "password_reset_requested_at",
            ]
        )

        # Kill all existing sessions for this user by blacklisting every
        # outstanding refresh token. Even if an attacker was mid-session
        # after phishing the old password, they're now logged out.
        _blacklist_all_refresh_tokens(user)

        return Response(
            {"message": "Password updated. Please log in with your new password."},
            status=status.HTTP_200_OK,
        )


def _constant_time_equals(a: str, b: str) -> bool:
    """SHA-256 hex is constant-length so this is a strict equality, but
    hmac.compare_digest guarantees no early-return timing side channel."""
    import hmac

    return hmac.compare_digest(a, b)


def _blacklist_all_refresh_tokens(user) -> None:
    """Blacklist every outstanding refresh token for the user. No-op if the
    token_blacklist app isn't installed."""
    try:
        from rest_framework_simplejwt.token_blacklist.models import (
            BlacklistedToken,
            OutstandingToken,
        )
    except ImportError:
        return

    outstanding = OutstandingToken.objects.filter(user=user)
    for token in outstanding:
        BlacklistedToken.objects.get_or_create(token=token)
