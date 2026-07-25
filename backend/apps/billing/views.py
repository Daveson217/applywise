from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import PLAN_LIMITS, Subscription
from .serializers import SubscriptionSerializer


PLANS_INFO = [
    {
        "name": "free",
        "display_name": "Free",
        "price_monthly": 0,
        "limits": PLAN_LIMITS["free"],
        "features": [
            "25 applications",
            "5 watchlist companies",
            "2 CV versions",
            "5 AI cover letters/mo",
            "Daily job monitoring",
        ],
    },
    {
        "name": "pro",
        "display_name": "Pro",
        "price_monthly": 4,
        "limits": PLAN_LIMITS["pro"],
        "features": [
            "Unlimited applications",
            "25 watchlist companies",
            "10 CV versions",
            "50 AI cover letters/mo",
            "All LLM providers",
            "4-hour monitoring",
            "CSV/JSON export",
            "SMS notifications",
        ],
    },
    {
        "name": "premium",
        "display_name": "Premium",
        "price_monthly": 10,
        "limits": PLAN_LIMITS["premium"],
        "features": [
            "Everything in Pro",
            "Unlimited everything",
            "Hourly monitoring",
            "Priority support",
            "API access",
        ],
    },
]


class PlansView(APIView):
    def get(self, request):
        return Response(PLANS_INFO)


class SubscriptionView(APIView):
    def get(self, request):
        sub, created = Subscription.objects.get_or_create(
            user=request.user,
            defaults={"plan": "free", "status": "active"},
        )
        return Response(SubscriptionSerializer(sub).data)


class CheckoutView(APIView):
    """Create a Stripe Checkout Session for an upgrade.

    Returns 503 if Stripe is not configured. A clear "service unavailable"
    is safer than returning a fake URL that might be clicked and trusted.
    """

    def post(self, request):
        from django.conf import settings

        plan = request.data.get("plan")
        if plan not in ("pro", "premium"):
            return Response(
                {"error": "Invalid plan"}, status=status.HTTP_400_BAD_REQUEST
            )

        stripe_key = getattr(settings, "STRIPE_SECRET_KEY", "")
        if not stripe_key:
            return Response(
                {
                    "error": "Billing is not configured on this server.",
                    "configured": False,
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # TODO: when stripe SDK is installed, create a real Checkout Session.
        # Until then, refuse rather than redirect to a placeholder.
        return Response(
            {
                "error": "Billing endpoint not yet implemented.",
                "configured": True,
            },
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )


class BillingPortalView(APIView):
    def post(self, request):
        from django.conf import settings

        if not getattr(settings, "STRIPE_SECRET_KEY", ""):
            return Response(
                {"error": "Billing is not configured on this server."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response(
            {"error": "Billing portal not yet implemented."},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )


class UsageView(APIView):
    """Return current usage vs limits for every quota. Frontend uses this to
    show progress bars and disable buttons preemptively."""

    def get(self, request):
        from .quotas import get_usage_summary

        return Response(get_usage_summary(request.user))
