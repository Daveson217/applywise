import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

from apps.billing.models import PLAN_LIMITS, Subscription
from apps.billing.permissions import get_user_limits, get_user_plan

User = get_user_model()

PLANS_URL = "/api/billing/plans/"
SUB_URL = "/api/billing/subscription/"
CHECKOUT_URL = "/api/billing/checkout/"
PORTAL_URL = "/api/billing/portal/"


@pytest.mark.django_db
class TestPlans:
    def test_list_plans(self, authenticated_client):
        response = authenticated_client.get(PLANS_URL)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3
        names = [p["name"] for p in response.data]
        assert "free" in names
        assert "pro" in names
        assert "premium" in names

    def test_plan_has_features(self, authenticated_client):
        response = authenticated_client.get(PLANS_URL)
        for plan in response.data:
            assert len(plan["features"]) > 0


@pytest.mark.django_db
class TestSubscription:
    def test_get_subscription_creates_default(self, authenticated_client):
        response = authenticated_client.get(SUB_URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["plan"] == "free"
        assert response.data["status"] == "active"

    def test_subscription_has_limits(self, authenticated_client):
        response = authenticated_client.get(SUB_URL)
        assert "limits" in response.data
        assert response.data["limits"]["max_applications"] == 25


@pytest.mark.django_db
class TestCheckout:
    def test_checkout_valid_plan_returns_503_when_unconfigured(self, authenticated_client):
        # No STRIPE_SECRET_KEY in tests → must refuse, not return a fake URL.
        # Previously this returned a placeholder which would have let users
        # think they were entering real Stripe checkout.
        response = authenticated_client.post(CHECKOUT_URL, {"plan": "pro"})
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert response.data.get("configured") is False

    def test_checkout_invalid_plan(self, authenticated_client):
        response = authenticated_client.post(CHECKOUT_URL, {"plan": "invalid"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_checkout_free_plan(self, authenticated_client):
        response = authenticated_client.post(CHECKOUT_URL, {"plan": "free"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestPermissions:
    def test_default_plan_is_free(self, user):
        assert get_user_plan(user) == "free"

    def test_pro_plan_detected(self, user):
        Subscription.objects.create(user=user, plan="pro", status="active")
        assert get_user_plan(user) == "pro"

    def test_limits_for_free(self, user):
        limits = get_user_limits(user)
        assert limits["max_applications"] == 25
        assert limits["csv_export"] is False

    def test_limits_for_pro(self, user):
        Subscription.objects.create(user=user, plan="pro", status="active")
        limits = get_user_limits(user)
        assert limits["max_applications"] is None
        assert limits["csv_export"] is True

    def test_check_limit(self, user):
        sub = Subscription.objects.create(user=user, plan="free", status="active")
        assert sub.check_limit("max_applications", 24) is True
        assert sub.check_limit("max_applications", 25) is False
