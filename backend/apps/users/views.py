import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import generics, serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import MeSerializer, RegisterSerializer, UserSerializer

logger = logging.getLogger(__name__)

User = get_user_model()


class LoginRateThrottle(AnonRateThrottle):
    """Tight per-IP throttle on login attempts. Prevents brute-force."""

    scope = "auth"


class RegisterRateThrottle(AnonRateThrottle):
    """Throttle account creation per IP. Prevents bulk-signup spam."""

    scope = "auth"


class ThrottledTokenObtainPairView(TokenObtainPairView):
    """Login endpoint with brute-force protection."""

    throttle_classes = [LoginRateThrottle]


class RegisterView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    throttle_classes = [RegisterRateThrottle]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        user_serializer = UserSerializer(user)

        return Response(
            {
                "user": user_serializer.data,
                "tokens": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                },
            },
            status=status.HTTP_201_CREATED,
        )


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = MeSerializer

    def get_object(self):
        return self.request.user


class LogoutView(generics.GenericAPIView):
    """Blacklist a refresh token so it can no longer be used.

    The access token (15-min lifetime) will still work until expiry — clients
    should drop it immediately on the frontend. Real logout is achieved by
    invalidating the refresh.
    """

    def post(self, request):
        refresh = request.data.get("refresh")
        if not refresh:
            return Response(
                {"error": "refresh token required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            RefreshToken(refresh).blacklist()
        except TokenError:
            # Already blacklisted or malformed — treat as success
            pass
        return Response(status=status.HTTP_205_RESET_CONTENT)


class PasswordChangeThrottle(UserRateThrottle):
    """Throttle change-password attempts per user. Prevents someone with
    a stolen access token from grinding through passwords to figure out
    the current one via error-differentiation."""

    scope = "auth"


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(min_length=1, max_length=128)
    new_password = serializers.CharField(min_length=8, max_length=128)

    def validate_new_password(self, value):
        # Run Django's password validators (min length, similarity, common
        # passwords, all-numeric)
        validate_password(value, user=self.context.get("user"))
        return value


class PasswordChangeView(APIView):
    """Change password while authenticated.

    Requires:
      - Valid access token (regular auth)
      - Current password (proof the session isn't stolen)
      - New password meets strength requirements

    On success:
      - Password is updated
      - ALL other refresh tokens are blacklisted (kill any other sessions
        the attacker may already have — the same defense we use on reset)
      - The caller keeps their current session (we don't blacklist THEIR
        refresh token — that would be annoying UX). If they want to log
        out other devices only, this is the right behavior.
    """

    throttle_classes = [PasswordChangeThrottle]

    def post(self, request):
        serializer = PasswordChangeSerializer(
            data=request.data, context={"user": request.user}
        )
        serializer.is_valid(raise_exception=True)

        current = serializer.validated_data["current_password"]
        new = serializer.validated_data["new_password"]

        # Verify current password — use check_password (constant-time)
        if not request.user.check_password(current):
            # Same 400 response as validation errors — don't reveal that
            # the current password specifically was wrong via a different
            # status code
            return Response(
                {"current_password": ["Current password is incorrect."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Refuse same-as-old password
        if request.user.check_password(new):
            return Response(
                {"new_password": ["New password must be different from the current one."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        request.user.set_password(new)
        request.user.save(update_fields=["password"])

        # Kill any OTHER active sessions. Get the caller's own refresh
        # token from the request (if provided) so we can preserve it.
        _blacklist_other_refresh_tokens(request.user, keep_refresh=request.data.get("current_refresh"))

        logger.info(f"Password changed for user id={request.user.id}")

        return Response(
            {"message": "Password updated."},
            status=status.HTTP_200_OK,
        )


def _blacklist_other_refresh_tokens(user, keep_refresh: str | None) -> None:
    """Blacklist all refresh tokens for `user` except `keep_refresh` (if any)."""
    try:
        from rest_framework_simplejwt.token_blacklist.models import (
            BlacklistedToken,
            OutstandingToken,
        )
    except ImportError:
        return

    keep_jti = None
    if keep_refresh:
        try:
            keep_jti = RefreshToken(keep_refresh).get("jti")
        except TokenError:
            keep_jti = None

    for token in OutstandingToken.objects.filter(user=user):
        if keep_jti and token.jti == keep_jti:
            continue
        BlacklistedToken.objects.get_or_create(token=token)
