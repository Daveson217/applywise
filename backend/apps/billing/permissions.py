from rest_framework.permissions import BasePermission

from .models import PLAN_LIMITS


def get_user_plan(user):
    try:
        sub = user.subscription
        if sub.is_active:
            return sub.plan
    except Exception:
        pass
    return "free"


def get_user_limits(user):
    plan = get_user_plan(user)
    return PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])


class HasProPlan(BasePermission):
    message = "This feature requires a Pro or Premium subscription."

    def has_permission(self, request, view):
        plan = get_user_plan(request.user)
        return plan in ("pro", "premium")


class HasPremiumPlan(BasePermission):
    message = "This feature requires a Premium subscription."

    def has_permission(self, request, view):
        plan = get_user_plan(request.user)
        return plan == "premium"


class CanExportData(BasePermission):
    message = "CSV/JSON export requires a Pro or Premium subscription."

    def has_permission(self, request, view):
        limits = get_user_limits(request.user)
        return limits.get("csv_export", False)
