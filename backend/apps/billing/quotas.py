"""Quota enforcement utilities.

Single source of truth for "can this user do X right now?" Limits are
defined in apps.billing.models.PLAN_LIMITS and checked here. Views call
`check_quota()` and get back an `Allowed` (proceed) or `Denied` (return 403).

Why a utility instead of a DRF permission class:
- AI quotas depend on month-rolling counts, which permission classes can't
  express cleanly when has_permission() needs both the user AND the feature
  name without action context.
- Resource quotas (max_applications, max_watchlist, max_cv_versions) check
  the user's current count, which permission_classes also can't see.

Single function used by all views:
    check_quota(user, key, current_count=None, feature=None)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from django.conf import settings
from django.utils import timezone as django_timezone

from .models import PLAN_LIMITS
from .permissions import get_user_limits, get_user_plan


def payments_enabled() -> bool:
    """Master switch. When False, every quota check returns 'allowed'.

    Read at call time (not import time) so tests can flip the setting
    via `@override_settings` without needing to reload this module.
    """
    return bool(getattr(settings, "PAYMENTS_ENABLED", False))


def _unlocked_result(plan: str = "premium") -> "QuotaResult":
    """Shape returned when PAYMENTS_ENABLED is False. All limits are None
    so the frontend renders 'unlimited' badges rather than confusing
    N/M progress bars."""
    return QuotaResult(allowed=True, plan=plan, limit=None, used=None)

# Map AI feature name → PLAN_LIMITS key for monthly cap
AI_FEATURE_LIMIT_KEYS = {
    "cover_letter": "max_cover_letters_monthly",
    "qa": "max_qa_monthly",
    "ats_score": "max_ats_scores_monthly",
    # fit_score has no monthly cap (free unlimited per spec — but ats_score does)
    "fit_score": None,
    "suggestions": None,
}


@dataclass
class QuotaResult:
    allowed: bool
    reason: str = ""
    limit: int | None = None
    used: int | None = None
    plan: str = "free"

    @property
    def remaining(self) -> int | None:
        if self.limit is None or self.used is None:
            return None
        return max(0, self.limit - self.used)


def _month_start_utc() -> datetime:
    """First-of-month at 00:00 UTC for the current calendar month."""
    now = django_timezone.now().astimezone(timezone.utc)
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def get_monthly_ai_usage(user, feature: str) -> int:
    """Count AIUsageLog rows for this user + feature within the current month."""
    # Local import — avoid circular dependency
    from apps.ai.models import AIUsageLog

    return AIUsageLog.objects.filter(
        user=user,
        feature=feature,
        timestamp__gte=_month_start_utc(),
    ).count()


def reserve_ai_quota(user, feature: str) -> QuotaResult:
    """Atomically check + reserve a slot for an AI generation.

    Race-safe alternative to `check_ai_quota`. Wraps the check + a pending
    AIUsageLog insert in a transaction with row-level locking on the user,
    so two concurrent requests can't both pass a 4/5 check then both create
    a 5th and 6th log.

    Returns QuotaResult with `allowed=True` if reserved, False if over cap.
    The caller MUST update the placeholder log with real token counts after
    the LLM call completes (`finalize_ai_reservation`).
    """
    from django.contrib.auth import get_user_model
    from django.db import transaction

    from apps.ai.models import AIUsageLog

    # Payments off — skip locking + reservation. Still create a usage-log
    # row so admin dashboards + get_usage_summary reflect real usage even
    # when unbounded.
    if not payments_enabled():
        log = AIUsageLog.objects.create(
            user=user, feature=feature, provider="pending",
            model="pending", input_tokens=0, output_tokens=0,
        )
        result = _unlocked_result()
        result.reservation_id = log.pk  # type: ignore[attr-defined]
        return result

    User = get_user_model()

    with transaction.atomic():
        # Row-lock on the user row prevents any other request from this user
        # from entering this block until we commit/rollback.
        User.objects.select_for_update().get(pk=user.pk)

        result = check_ai_quota(user, feature)
        if not result.allowed:
            return result

        # Pre-create a placeholder log row. It "counts" toward the cap as
        # soon as the transaction commits, so a parallel request entering
        # this block next will see the new count.
        log = AIUsageLog.objects.create(
            user=user, feature=feature, provider="pending",
            model="pending", input_tokens=0, output_tokens=0,
        )

    result.used = (result.used or 0) + 1
    result.reservation_id = log.pk  # type: ignore[attr-defined]
    return result


def finalize_ai_reservation(
    reservation_id: int, provider: str, model: str,
    input_tokens: int, output_tokens: int,
) -> None:
    """Update a reserved AIUsageLog row with real token counts. Idempotent."""
    from apps.ai.models import AIUsageLog

    AIUsageLog.objects.filter(pk=reservation_id).update(
        provider=provider,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )


def release_ai_reservation(reservation_id: int) -> None:
    """Delete a reserved AIUsageLog row (call on task failure)."""
    from apps.ai.models import AIUsageLog

    AIUsageLog.objects.filter(pk=reservation_id).delete()


def reserve_resource_quota(user, resource_key: str, model_cls) -> QuotaResult:
    """Atomically check resource cap with row-locking on the user.

    Caller should perform the create() inside the same transaction.
    Usage:
        with transaction.atomic():
            result = reserve_resource_quota(user, "max_applications", Application)
            if not result.allowed:
                return error_response
            Application.objects.create(user=user, ...)
    """
    from django.contrib.auth import get_user_model
    from django.db import transaction

    if not payments_enabled():
        return _unlocked_result()

    User = get_user_model()

    # Already in atomic block from caller — just lock the user
    User.objects.select_for_update().get(pk=user.pk)
    current_count = model_cls.objects.filter(user=user).count()
    return check_resource_quota(user, resource_key, current_count)


def check_ai_quota(user, feature: str) -> QuotaResult:
    """Can the user invoke this AI feature right now (monthly cap)?"""
    if not payments_enabled():
        return _unlocked_result()
    plan = get_user_plan(user)
    limits = get_user_limits(user)

    limit_key = AI_FEATURE_LIMIT_KEYS.get(feature)
    if limit_key is None:
        return QuotaResult(allowed=True, plan=plan)

    monthly_limit = limits.get(limit_key)
    if monthly_limit is None:
        return QuotaResult(allowed=True, plan=plan)  # unlimited

    used = get_monthly_ai_usage(user, feature)
    if used >= monthly_limit:
        return QuotaResult(
            allowed=False,
            reason=(
                f"You've used your {monthly_limit} {feature.replace('_', ' ')} "
                f"generations for this month on the {plan.capitalize()} plan. "
                f"Upgrade for more."
            ),
            limit=monthly_limit,
            used=used,
            plan=plan,
        )
    return QuotaResult(allowed=True, limit=monthly_limit, used=used, plan=plan)


def check_provider_allowed(user, provider: str, model: str | None = None) -> QuotaResult:
    """Free tier can only use Gemini Flash. Pro/Premium can use anything."""
    if not payments_enabled():
        return _unlocked_result()
    plan = get_user_plan(user)
    limits = get_user_limits(user)

    allowed_providers = limits.get("allowed_providers", [])
    if allowed_providers and provider not in allowed_providers:
        return QuotaResult(
            allowed=False,
            reason=(
                f"The {provider} provider is not available on the "
                f"{plan.capitalize()} plan. Upgrade to access all providers."
            ),
            plan=plan,
        )

    allowed_models = limits.get("allowed_models")
    if allowed_models and model and model not in allowed_models:
        return QuotaResult(
            allowed=False,
            reason=(
                f"The {model} model is not available on the "
                f"{plan.capitalize()} plan. Upgrade to access all models."
            ),
            plan=plan,
        )
    return QuotaResult(allowed=True, plan=plan)


def check_resource_quota(user, resource_key: str, current_count: int) -> QuotaResult:
    """Generic resource cap check (applications, watchlist, CV versions, tags).

    `resource_key` is a PLAN_LIMITS key like 'max_applications'.
    Pass the current row count for the user.
    """
    if not payments_enabled():
        return _unlocked_result()
    plan = get_user_plan(user)
    limits = get_user_limits(user)
    limit = limits.get(resource_key)

    if limit is None:
        return QuotaResult(allowed=True, plan=plan)

    if current_count >= limit:
        human = resource_key.replace("max_", "").replace("_", " ")
        return QuotaResult(
            allowed=False,
            reason=(
                f"You've reached your limit of {limit} {human} on the "
                f"{plan.capitalize()} plan. Upgrade for more."
            ),
            limit=limit,
            used=current_count,
            plan=plan,
        )
    return QuotaResult(allowed=True, limit=limit, used=current_count, plan=plan)


def get_usage_summary(user) -> dict:
    """Snapshot of all quotas for the user — used by the frontend to show
    progress bars and disable buttons before the user clicks them.

    When PAYMENTS_ENABLED is False, every `limit` is None (frontend renders
    as "unlimited") and `payments_enabled: False` tells the pricing page
    to hide upgrade prompts. Real `used` counts still surface so admins
    can see activity even in beta mode.
    """
    from apps.applications.models import Application, CVVersion
    from apps.watchlist.models import WatchlistCompany

    enabled = payments_enabled()
    plan = get_user_plan(user)
    limits = get_user_limits(user)

    apps_count = Application.objects.filter(user=user).count()
    watchlist_count = WatchlistCompany.objects.filter(user=user).count()
    cv_count = CVVersion.objects.filter(user=user).count()

    cover_letters_used = get_monthly_ai_usage(user, "cover_letter")
    qa_used = get_monthly_ai_usage(user, "qa")
    ats_used = get_monthly_ai_usage(user, "ats_score")

    def _limit(key: str) -> int | None:
        # None means "unlimited" — either the plan's own limit is None,
        # or payments are globally disabled.
        return None if not enabled else limits.get(key)

    def _providers() -> list[str]:
        # When payments are off, expose all providers so the frontend
        # dropdown isn't artificially restricted.
        if not enabled:
            return ["gemini", "openai", "anthropic"]
        return limits.get("allowed_providers", [])

    return {
        "payments_enabled": enabled,
        "plan": plan if enabled else "beta",
        "resources": {
            "applications": {"used": apps_count, "limit": _limit("max_applications")},
            "watchlist": {"used": watchlist_count, "limit": _limit("max_watchlist")},
            "cv_versions": {"used": cv_count, "limit": _limit("max_cv_versions")},
        },
        "ai_monthly": {
            "cover_letter": {"used": cover_letters_used, "limit": _limit("max_cover_letters_monthly")},
            "qa": {"used": qa_used, "limit": _limit("max_qa_monthly")},
            "ats_score": {"used": ats_used, "limit": _limit("max_ats_scores_monthly")},
        },
        "providers": _providers(),
    }
