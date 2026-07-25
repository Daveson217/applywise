"""Quota enforcement tests covering the full matrix:
- AI monthly caps (cover_letter, qa, ats_score)
- Provider gating (free tier = gemini only)
- Resource caps (applications, watchlist, cv_versions)
- Cross-month rollover (last month's usage doesn't count this month)
- Pro/Premium bypass
"""

from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework import status

from apps.ai.models import AIUsageLog
from apps.applications.models import Application, CVVersion
from apps.billing.models import Subscription
from apps.billing.quotas import (
    check_ai_quota,
    check_provider_allowed,
    check_resource_quota,
    get_monthly_ai_usage,
    get_usage_summary,
)
from apps.watchlist.models import WatchlistCompany


# ─────────────────────────────────────────────────────────────────────────────
# Unit tests on the quota functions themselves
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestAIQuotaFunctions:
    def test_free_tier_under_limit(self, user):
        result = check_ai_quota(user, "cover_letter")
        assert result.allowed
        assert result.limit == 5  # free tier monthly cap
        assert result.used == 0
        assert result.remaining == 5

    def test_free_tier_at_limit(self, user):
        for _ in range(5):
            AIUsageLog.objects.create(
                user=user, feature="cover_letter", provider="gemini",
                model="gemini-2.5-flash", input_tokens=100, output_tokens=200,
            )
        result = check_ai_quota(user, "cover_letter")
        assert not result.allowed
        assert "5" in result.reason
        assert "Free" in result.reason

    def test_pro_tier_higher_limit(self, user):
        Subscription.objects.create(user=user, plan="pro", status="active")
        for _ in range(20):
            AIUsageLog.objects.create(
                user=user, feature="cover_letter", provider="openai",
                model="gpt-4o", input_tokens=100, output_tokens=200,
            )
        result = check_ai_quota(user, "cover_letter")
        assert result.allowed
        assert result.limit == 50  # pro monthly cap
        assert result.used == 20

    def test_premium_unlimited(self, user):
        Subscription.objects.create(user=user, plan="premium", status="active")
        for _ in range(100):
            AIUsageLog.objects.create(
                user=user, feature="cover_letter", provider="openai",
                model="gpt-4o", input_tokens=100, output_tokens=200,
            )
        result = check_ai_quota(user, "cover_letter")
        assert result.allowed
        assert result.limit is None

    def test_fit_score_always_allowed(self, user):
        # fit_score has no monthly cap in PLAN_LIMITS mapping
        for _ in range(50):
            AIUsageLog.objects.create(
                user=user, feature="fit_score", provider="gemini",
                model="gemini-2.5-flash", input_tokens=100, output_tokens=200,
            )
        result = check_ai_quota(user, "fit_score")
        assert result.allowed

    def test_cross_month_rollover(self, user):
        """Last month's usage shouldn't count toward this month."""
        last_month = timezone.now() - timedelta(days=35)
        for _ in range(10):
            log = AIUsageLog.objects.create(
                user=user, feature="cover_letter", provider="gemini",
                model="gemini-2.5-flash", input_tokens=100, output_tokens=200,
            )
            AIUsageLog.objects.filter(pk=log.pk).update(timestamp=last_month)

        assert get_monthly_ai_usage(user, "cover_letter") == 0
        result = check_ai_quota(user, "cover_letter")
        assert result.allowed
        assert result.used == 0


@pytest.mark.django_db
class TestProviderGating:
    def test_free_allowed_gemini(self, user):
        result = check_provider_allowed(user, "gemini")
        assert result.allowed

    def test_free_blocked_openai(self, user):
        result = check_provider_allowed(user, "openai")
        assert not result.allowed
        assert "openai" in result.reason.lower()
        assert "Free" in result.reason

    def test_free_blocked_anthropic(self, user):
        result = check_provider_allowed(user, "anthropic")
        assert not result.allowed

    def test_free_blocked_non_default_gemini_model(self, user):
        # Free tier locked to gemini-2.5-flash specifically
        result = check_provider_allowed(user, "gemini", "gemini-2.0-pro")
        assert not result.allowed
        assert "model" in result.reason.lower()

    def test_pro_allows_all_providers(self, user):
        Subscription.objects.create(user=user, plan="pro", status="active")
        for provider in ("gemini", "openai", "anthropic"):
            assert check_provider_allowed(user, provider).allowed

    def test_premium_allows_all_providers(self, user):
        Subscription.objects.create(user=user, plan="premium", status="active")
        for provider in ("gemini", "openai", "anthropic"):
            assert check_provider_allowed(user, provider).allowed


@pytest.mark.django_db
class TestResourceQuotas:
    def test_free_app_limit_under(self, user):
        result = check_resource_quota(user, "max_applications", 10)
        assert result.allowed
        assert result.limit == 25

    def test_free_app_limit_at_cap(self, user):
        result = check_resource_quota(user, "max_applications", 25)
        assert not result.allowed
        assert "25" in result.reason

    def test_pro_app_unlimited(self, user):
        Subscription.objects.create(user=user, plan="pro", status="active")
        result = check_resource_quota(user, "max_applications", 1000)
        assert result.allowed

    def test_free_watchlist_limit(self, user):
        result = check_resource_quota(user, "max_watchlist", 5)
        assert not result.allowed

    def test_free_cv_limit(self, user):
        result = check_resource_quota(user, "max_cv_versions", 2)
        assert not result.allowed


@pytest.mark.django_db
class TestUsageSummary:
    def test_summary_shape(self, user):
        summary = get_usage_summary(user)
        assert summary["plan"] == "free"
        assert "resources" in summary
        assert "ai_monthly" in summary
        assert "applications" in summary["resources"]
        assert summary["resources"]["applications"]["limit"] == 25
        assert summary["ai_monthly"]["cover_letter"]["limit"] == 5

    def test_summary_counts_real_resources(self, user):
        Application.objects.create(
            user=user, company="X", role="Y", job_type="fulltime"
        )
        WatchlistCompany.objects.create(user=user, name="W")
        summary = get_usage_summary(user)
        assert summary["resources"]["applications"]["used"] == 1
        assert summary["resources"]["watchlist"]["used"] == 1


# ─────────────────────────────────────────────────────────────────────────────
# End-to-end API tests — verify views return 403 with helpful errors
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestAIEndpointEnforcement:
    def _make_cv(self, user):
        return CVVersion.objects.create(
            user=user, name="T", file="t.pdf", extracted_text="skills: python"
        )

    def test_cover_letter_blocks_over_quota(self, authenticated_client, user):
        cv = self._make_cv(user)
        for _ in range(5):
            AIUsageLog.objects.create(
                user=user, feature="cover_letter", provider="gemini",
                model="gemini-2.5-flash", input_tokens=100, output_tokens=200,
            )

        response = authenticated_client.post(
            "/api/ai/cover-letter/",
            {
                "cv_version_id": cv.id,
                "company": "Stripe",
                "job_title": "Engineer",
                "job_description": "Build cool stuff",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["limit"] == 5
        assert response.data["used"] == 5
        assert "upgrade_url" in response.data

    def test_cover_letter_blocks_paid_provider_on_free(
        self, authenticated_client, user
    ):
        cv = self._make_cv(user)
        response = authenticated_client.post(
            "/api/ai/cover-letter/",
            {
                "cv_version_id": cv.id,
                "company": "Stripe",
                "job_title": "Engineer",
                "job_description": "Build cool stuff",
                "provider": "openai",
                "model": "gpt-4o",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "openai" in response.data["error"].lower()

    def test_qa_blocks_over_quota(self, authenticated_client, user):
        cv = self._make_cv(user)
        for _ in range(10):
            AIUsageLog.objects.create(
                user=user, feature="qa", provider="gemini",
                model="gemini-2.5-flash", input_tokens=50, output_tokens=150,
            )
        response = authenticated_client.post(
            "/api/ai/question-answer/",
            {"cv_version_id": cv.id, "question": "Why us?"},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_ats_score_blocks_over_quota(self, authenticated_client, user):
        cv = self._make_cv(user)
        for _ in range(10):
            AIUsageLog.objects.create(
                user=user, feature="ats_score", provider="gemini",
                model="gemini-2.5-flash", input_tokens=100, output_tokens=200,
            )
        response = authenticated_client.post(
            "/api/ai/ats-score/",
            {"cv_version_id": cv.id, "job_description": "Build stuff"},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_fit_score_provider_gated_for_free(
        self, authenticated_client, user
    ):
        cv = self._make_cv(user)
        # Free user trying to use OpenAI is blocked before the task runs
        blocked = authenticated_client.post(
            "/api/ai/fit-score/",
            {
                "cv_version_id": cv.id,
                "job_description": "x",
                "provider": "openai",
                "model": "gpt-4o",
            },
            format="json",
        )
        assert blocked.status_code == status.HTTP_403_FORBIDDEN
        assert "openai" in blocked.data["error"].lower()


@pytest.mark.django_db
class TestResourceEndpointEnforcement:
    def test_create_application_blocks_at_limit(
        self, authenticated_client, user
    ):
        for i in range(25):
            Application.objects.create(
                user=user, company=f"C{i}", role="R", job_type="fulltime"
            )
        response = authenticated_client.post(
            "/api/applications/",
            {"company": "26th", "role": "R", "job_type": "fulltime"},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["limit"] == 25
        assert "upgrade_url" in response.data

    def test_create_application_allowed_for_pro(
        self, authenticated_client, user
    ):
        Subscription.objects.create(user=user, plan="pro", status="active")
        for i in range(25):
            Application.objects.create(
                user=user, company=f"C{i}", role="R", job_type="fulltime"
            )
        response = authenticated_client.post(
            "/api/applications/",
            {"company": "26th", "role": "R", "job_type": "fulltime"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_watchlist_blocks_at_limit(
        self, authenticated_client, user
    ):
        for i in range(5):
            WatchlistCompany.objects.create(user=user, name=f"Co{i}")
        response = authenticated_client.post(
            "/api/watchlist/", {"name": "6th"}, format="json"
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["limit"] == 5

    def test_create_cv_blocks_at_limit(self, authenticated_client, user):
        for i in range(2):
            CVVersion.objects.create(
                user=user, name=f"v{i}", file=f"f{i}.pdf"
            )
        # Multipart upload — but should 403 before parsing
        response = authenticated_client.post(
            "/api/cv/",
            {"name": "v3", "file": ""},
            format="multipart",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestUsageEndpoint:
    def test_usage_endpoint(self, authenticated_client, user):
        Application.objects.create(
            user=user, company="X", role="Y", job_type="fulltime"
        )
        AIUsageLog.objects.create(
            user=user, feature="cover_letter", provider="gemini",
            model="gemini-2.5-flash", input_tokens=100, output_tokens=200,
        )
        response = authenticated_client.get("/api/billing/usage/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["plan"] == "free"
        assert response.data["resources"]["applications"]["used"] == 1
        assert response.data["resources"]["applications"]["limit"] == 25
        assert response.data["ai_monthly"]["cover_letter"]["used"] == 1
        assert response.data["ai_monthly"]["cover_letter"]["limit"] == 5
