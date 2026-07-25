from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views
from .password_reset import PasswordResetConfirmView, PasswordResetRequestView
from .social_auth import GoogleAuthView, LinkedInAuthView

urlpatterns = [
    path("auth/register/", views.RegisterView.as_view(), name="register"),
    path(
        "auth/login/",
        views.ThrottledTokenObtainPairView.as_view(),
        name="token-obtain-pair",
    ),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("auth/logout/", views.LogoutView.as_view(), name="logout"),
    path(
        "auth/password/change/",
        views.PasswordChangeView.as_view(),
        name="password-change",
    ),
    path(
        "auth/password/reset-request/",
        PasswordResetRequestView.as_view(),
        name="password-reset-request",
    ),
    path(
        "auth/password/reset-confirm/",
        PasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),
    path("auth/social/google/", GoogleAuthView.as_view(), name="social-google"),
    path("auth/social/linkedin/", LinkedInAuthView.as_view(), name="social-linkedin"),
    path("users/me/", views.MeView.as_view(), name="me"),
]
