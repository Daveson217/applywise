from django.conf import settings
from django.db import models

PLAN_CHOICES = [
    ("free", "Free"),
    ("pro", "Pro"),
    ("premium", "Premium"),
]

SUB_STATUS_CHOICES = [
    ("active", "Active"),
    ("trialing", "Trialing"),
    ("past_due", "Past Due"),
    ("canceled", "Canceled"),
    ("incomplete", "Incomplete"),
]

PLAN_LIMITS = {
    "free": {
        "max_applications": 25,
        "max_watchlist": 5,
        "max_cv_versions": 2,
        "max_cover_letters_monthly": 5,
        "max_qa_monthly": 10,
        "max_ats_scores_monthly": 10,
        "monitoring_interval_hours": 24,
        "allowed_providers": [
            "gemini",
        ],
        "allowed_models": ["gemini-2.5-flash"],
        "csv_export": False,
        "sms_notifications": False,
        "offer_comparison": False,
    },
    "pro": {
        "max_applications": None,
        "max_watchlist": 25,
        "max_cv_versions": 10,
        "max_cover_letters_monthly": 50,
        "max_qa_monthly": 100,
        "max_ats_scores_monthly": None,
        "monitoring_interval_hours": 4,
        "allowed_providers": ["gemini", "openai", "anthropic"],
        "allowed_models": None,
        "csv_export": True,
        "sms_notifications": True,
        "offer_comparison": True,
    },
    "premium": {
        "max_applications": None,
        "max_watchlist": None,
        "max_cv_versions": None,
        "max_cover_letters_monthly": None,
        "max_qa_monthly": None,
        "max_ats_scores_monthly": None,
        "monitoring_interval_hours": 1,
        "allowed_providers": ["gemini", "openai", "anthropic"],
        "allowed_models": None,
        "csv_export": True,
        "sms_notifications": True,
        "offer_comparison": True,
    },
}


class Subscription(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscription",
    )
    stripe_customer_id = models.CharField(max_length=255, blank=True)
    stripe_subscription_id = models.CharField(max_length=255, blank=True)
    plan = models.CharField(max_length=10, choices=PLAN_CHOICES, default="free")
    status = models.CharField(max_length=20, choices=SUB_STATUS_CHOICES, default="active")
    current_period_end = models.DateTimeField(null=True, blank=True)
    trial_end = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} - {self.plan} ({self.status})"

    @property
    def is_active(self):
        return self.status in ("active", "trialing")

    @property
    def limits(self):
        return PLAN_LIMITS.get(self.plan, PLAN_LIMITS["free"])

    def check_limit(self, key: str, current_count: int) -> bool:
        limit = self.limits.get(key)
        if limit is None:
            return True
        return current_count < limit
