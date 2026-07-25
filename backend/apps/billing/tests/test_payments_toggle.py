"""Tests for the PAYMENTS_ENABLED master switch.

Covers:
- All quota check functions return `allowed=True` when payments are off
- Provider gating is bypassed
- Resource caps are bypassed
- Reservation still creates an AIUsageLog row (for admin visibility)
- Usage summary reports `payments_enabled: False` and all limits null
- CSV export skips its subscription check
- Enabling payments restores the enforcement
- Cross-endpoint: real API calls succeed past the free-tier caps when off
"""

import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework import status

from apps.ai.models import AIUsageLog
from apps.applications.models import Application, CVVersion
from apps.billing.models import Subscription
from apps.billing.quotas import (
    check_ai_quota,
    check_provider_allowed,
    check_resource_quota,
    get_usage_summary,
    payments_enabled,
    reserve_ai_quota,
)
from apps.watchlist.models import WatchlistCompany

User = get_user_model()


# ─────────────────────────────────────────────────────────────────────────────
# Unit tests on the quota functions
# ─────────────────────────────────────────────────────────────────────────────


class TestPaymentsEnabledFlag:
    @override_settings(PAYMENTS_ENABLED=False)
    def test_flag_reads_from_settings(self):
        assert payments_enabled() is False

    @override_settings(PAYMENTS_ENABLED=True)
    def test_flag_reflects_toggle(self):
        assert payments_enabled() is True


@pytest.mark.django_db
class TestQuotaBypassWhenDisabled:
    @override_settings(PAYMENTS_ENABLED=False)
    def test_ai_quota_always_allowed(self, user):
        # Even with 999 prior generations, free-tier cap of 5 doesn't apply
        for _ in range(999):
            AIUsageLog.objects.create(
                user=user,
                feature="cover_letter",
                provider="gemini",
                model="gemini-2.5-flash",
                input_tokens=1,
                output_tokens=1,
            )
        result = check_ai_quota(user, "cover_letter")
        assert result.allowed is True
        assert result.limit is None

    @override_settings(PAYMENTS_ENABLED=False)
    def test_provider_gating_bypassed(self, user):
        # Free user picks paid-tier provider — still allowed
        result = check_provider_allowed(user, "openai", "gpt-4o")
        assert result.allowed is True

    @override_settings(PAYMENTS_ENABLED=False)
    def test_resource_quota_bypassed(self, user):
        # Free-tier cap is 25 applications; pretend user has 1000
        result = check_resource_quota(user, "max_applications", 1000)
        assert result.allowed is True

    @override_settings(PAYMENTS_ENABLED=False)
    def test_reserve_still_creates_usage_log(self, user):
        # We still track usage — admins want to see it even in beta mode
        before = AIUsageLog.objects.filter(user=user).count()
        result = reserve_ai_quota(user, "cover_letter")
        assert result.allowed is True
        assert AIUsageLog.objects.filter(user=user).count() == before + 1
        assert result.reservation_id is not None  # type: ignore

    @override_settings(PAYMENTS_ENABLED=False)
    def test_reserve_returns_reservation_id(self, user):
        result = reserve_ai_quota(user, "qa")
        # Finalize / release must still work
        assert getattr(result, "reservation_id", None) is not None


@pytest.mark.django_db
class TestUsageSummaryShape:
    @override_settings(PAYMENTS_ENABLED=False)
    def test_summary_reports_disabled(self, user):
        summary = get_usage_summary(user)
        assert summary["payments_enabled"] is False
        assert summary["plan"] == "beta"
        # All limits null → frontend renders "unlimited"
        assert summary["resources"]["applications"]["limit"] is None
        assert summary["resources"]["watchlist"]["limit"] is None
        assert summary["resources"]["cv_versions"]["limit"] is None
        assert summary["ai_monthly"]["cover_letter"]["limit"] is None
        assert summary["ai_monthly"]["qa"]["limit"] is None
        assert summary["ai_monthly"]["ats_score"]["limit"] is None
        # All providers exposed
        assert set(summary["providers"]) == {"gemini", "openai", "anthropic"}

    @override_settings(PAYMENTS_ENABLED=True)
    def test_summary_reports_enabled_and_real_limits(self, user):
        summary = get_usage_summary(user)
        assert summary["payments_enabled"] is True
        assert summary["plan"] == "free"
        assert summary["resources"]["applications"]["limit"] == 25
        assert summary["ai_monthly"]["cover_letter"]["limit"] == 5
        assert summary["providers"] == ["gemini"]

    @override_settings(PAYMENTS_ENABLED=False)
    def test_summary_still_counts_actual_usage(self, user):
        # Even in beta mode, `used` reflects reality — admins need this
        Application.objects.create(user=user, company="X", role="Y", job_type="fulltime")
        AIUsageLog.objects.create(
            user=user,
            feature="cover_letter",
            provider="gemini",
            model="gemini-2.5-flash",
            input_tokens=10,
            output_tokens=10,
        )
        summary = get_usage_summary(user)
        assert summary["resources"]["applications"]["used"] == 1
        assert summary["ai_monthly"]["cover_letter"]["used"] == 1


# ─────────────────────────────────────────────────────────────────────────────
# End-to-end API tests — actual endpoints succeed past free-tier caps
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestAPIEndpointsWhenDisabled:
    @override_settings(PAYMENTS_ENABLED=False)
    def test_create_26th_application_allowed(self, authenticated_client, user):
        for i in range(25):
            Application.objects.create(user=user, company=f"C{i}", role="R", job_type="fulltime")
        # Free tier hard limit is 25 — this would normally 403
        response = authenticated_client.post(
            "/api/applications/",
            {"company": "26th", "role": "R", "job_type": "fulltime"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED

    @override_settings(PAYMENTS_ENABLED=False)
    def test_create_6th_watchlist_allowed(self, authenticated_client, user):
        for i in range(5):
            WatchlistCompany.objects.create(user=user, name=f"C{i}")
        response = authenticated_client.post("/api/watchlist/", {"name": "6th"}, format="json")
        assert response.status_code == status.HTTP_201_CREATED

    @override_settings(PAYMENTS_ENABLED=False)
    def test_cover_letter_openai_allowed_for_free_user(self, authenticated_client, user):
        # Free user picking OpenAI is normally 403 (provider gating).
        # We mock .delay so the eager Celery task doesn't call real OpenAI.
        from unittest.mock import patch

        cv = CVVersion.objects.create(user=user, name="CV", file="cv.pdf", extracted_text="skills")
        with patch("apps.ai.views.generate_cover_letter") as mock_task:
            mock_task.delay.return_value.id = "fake-task-id"
            response = authenticated_client.post(
                "/api/ai/cover-letter/",
                {
                    "cv_version_id": cv.id,
                    "company": "Google",
                    "job_title": "SWE",
                    "job_description": "code",
                    "provider": "openai",
                    "model": "gpt-4o",
                },
                format="json",
            )
        # 202 = queued past the provider gate. If payments were on this
        # would be 403 because free tier is Gemini-only.
        assert response.status_code == status.HTTP_202_ACCEPTED

    @override_settings(PAYMENTS_ENABLED=False)
    def test_csv_export_allowed_for_free_user(self, authenticated_client, user):
        # Normally requires Pro+ subscription
        response = authenticated_client.get("/api/applications/export/", {"type": "csv"})
        assert response.status_code == status.HTTP_200_OK

    @override_settings(PAYMENTS_ENABLED=False)
    def test_usage_endpoint_exposes_flag(self, authenticated_client):
        response = authenticated_client.get("/api/billing/usage/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["payments_enabled"] is False
        assert response.data["plan"] == "beta"


@pytest.mark.django_db
class TestPaymentsEnabledRestoresEnforcement:
    @override_settings(PAYMENTS_ENABLED=True)
    def test_when_enabled_free_tier_cap_enforced(self, authenticated_client, user):
        for i in range(25):
            Application.objects.create(user=user, company=f"C{i}", role="R", job_type="fulltime")
        response = authenticated_client.post(
            "/api/applications/",
            {"company": "26th", "role": "R", "job_type": "fulltime"},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @override_settings(PAYMENTS_ENABLED=True)
    def test_when_enabled_pro_user_bypasses_cap(self, authenticated_client, user):
        Subscription.objects.create(user=user, plan="pro", status="active")
        for i in range(25):
            Application.objects.create(user=user, company=f"C{i}", role="R", job_type="fulltime")
        response = authenticated_client.post(
            "/api/applications/",
            {"company": "26th", "role": "R", "job_type": "fulltime"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
