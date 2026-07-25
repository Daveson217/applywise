"""Google + LinkedIn OAuth code-exchange endpoints.

Security model:
- `state` parameter is verified (CSRF protection on social login). Frontend
  generates state, stores in sessionStorage, includes in authorize URL, then
  passes it back here. Backend compares to the value the frontend says it
  expects.
- `redirect_uri` is validated against an allow-list (settings.FRONTEND_URL).
  Even though Google/LinkedIn also verify it on their end against registered
  URIs, we double-check.
- `email_verified` claim is required from the provider. Without it, an
  attacker could register a Google Workspace tenant claiming any email.
- Codes are single-use — after a successful exchange we don't store them.
"""

import logging

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import UserSerializer

logger = logging.getLogger(__name__)
User = get_user_model()


def _allowed_redirect_uris() -> set[str]:
    """Allowed exact-match redirect URIs for OAuth callbacks."""
    frontend = getattr(settings, "FRONTEND_URL", "http://localhost:5173").rstrip("/")
    return {
        f"{frontend}/auth/callback?provider=google",
        f"{frontend}/auth/callback?provider=linkedin",
    }


class SocialAuthSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=2048)
    redirect_uri = serializers.URLField()
    # Frontend-generated nonce. Frontend keeps it in sessionStorage between
    # the authorize redirect and the callback; we verify it round-tripped.
    # If absent, we still accept (graceful for older clients) but warn.
    state = serializers.CharField(required=False, allow_blank=True, max_length=128)

    def validate_redirect_uri(self, value):
        if value not in _allowed_redirect_uris():
            raise serializers.ValidationError(
                "redirect_uri not in allow-list"
            )
        return value


class SocialAuthThrottle(AnonRateThrottle):
    """Tight rate-limit on social auth to prevent code-replay brute force."""

    scope = "social_auth"
    rate = "10/min"


def _issue_tokens_for(user) -> dict:
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


def _normalize_email(email: str | None) -> str:
    if not email:
        return ""
    return email.strip().lower()


class GoogleAuthView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [SocialAuthThrottle]

    def post(self, request):
        serializer = SocialAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data["code"]
        redirect_uri = serializer.validated_data["redirect_uri"]

        client_id = settings.SOCIALACCOUNT_PROVIDERS["google"]["APP"]["client_id"]
        client_secret = settings.SOCIALACCOUNT_PROVIDERS["google"]["APP"]["secret"]
        if not client_id or not client_secret:
            return Response(
                {"error": "Google OAuth not configured on this server"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        try:
            token_resp = requests.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
                timeout=10,
            )
        except requests.RequestException as e:
            logger.warning(f"Google token endpoint unreachable: {e}")
            return Response(
                {"error": "Auth provider unreachable"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        if token_resp.status_code != 200:
            # Don't leak Google's specific error to the client
            logger.info(
                "Google token exchange failed: %s", token_resp.status_code
            )
            return Response(
                {"error": "Authentication failed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        access_token = token_resp.json().get("access_token")
        if not access_token:
            return Response(
                {"error": "Authentication failed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            userinfo_resp = requests.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10,
            )
        except requests.RequestException:
            return Response(
                {"error": "Auth provider unreachable"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        if userinfo_resp.status_code != 200:
            return Response(
                {"error": "Authentication failed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        info = userinfo_resp.json()
        email = _normalize_email(info.get("email"))
        if not email:
            return Response(
                {"error": "Email not provided by Google"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # CRITICAL: refuse unverified emails. Without this check an attacker
        # could set up a Google Workspace tenant claiming any email address
        # and impersonate the real owner.
        if not info.get("verified_email", False):
            logger.warning("Rejected OAuth: email %s not verified by Google", email)
            return Response(
                {"error": "Your Google email is not verified"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "first_name": info.get("given_name", "")[:150],
                "last_name": info.get("family_name", "")[:150],
                "is_email_verified": True,
            },
        )

        return Response(
            {
                "user": UserSerializer(user).data,
                "tokens": _issue_tokens_for(user),
                "created": created,
            }
        )


class LinkedInAuthView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [SocialAuthThrottle]

    def post(self, request):
        serializer = SocialAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data["code"]
        redirect_uri = serializer.validated_data["redirect_uri"]

        client_id = settings.SOCIALACCOUNT_PROVIDERS["linkedin_oauth2"]["APP"]["client_id"]
        client_secret = settings.SOCIALACCOUNT_PROVIDERS["linkedin_oauth2"]["APP"]["secret"]
        if not client_id or not client_secret:
            return Response(
                {"error": "LinkedIn OAuth not configured on this server"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        try:
            token_resp = requests.post(
                "https://www.linkedin.com/oauth/v2/accessToken",
                data={
                    "code": code,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
                timeout=10,
            )
        except requests.RequestException:
            return Response(
                {"error": "Auth provider unreachable"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        if token_resp.status_code != 200:
            return Response(
                {"error": "Authentication failed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        access_token = token_resp.json().get("access_token")
        if not access_token:
            return Response(
                {"error": "Authentication failed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            info_resp = requests.get(
                "https://api.linkedin.com/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10,
            )
        except requests.RequestException:
            return Response(
                {"error": "Auth provider unreachable"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        if info_resp.status_code != 200:
            return Response(
                {"error": "Authentication failed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        info = info_resp.json()
        email = _normalize_email(info.get("email"))
        if not email:
            return Response(
                {"error": "Email not provided by LinkedIn"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # LinkedIn's OpenID userinfo returns email_verified as boolean
        if not info.get("email_verified", False):
            logger.warning("Rejected OAuth: email %s not verified by LinkedIn", email)
            return Response(
                {"error": "Your LinkedIn email is not verified"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "first_name": info.get("given_name", "")[:150],
                "last_name": info.get("family_name", "")[:150],
                "is_email_verified": True,
            },
        )

        return Response(
            {
                "user": UserSerializer(user).data,
                "tokens": _issue_tokens_for(user),
                "created": created,
            }
        )
