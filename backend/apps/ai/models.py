from django.conf import settings
from django.db import models

from apps.applications.models import Application, CVVersion

FEATURE_CHOICES = [
    ("cover_letter", "Cover Letter"),
    ("qa", "Question Answer"),
    ("fit_score", "Fit Score"),
    ("ats_score", "ATS Score"),
    ("suggestions", "Suggestions"),
]

PROVIDER_CHOICES = [
    ("gemini", "Google Gemini"),
    ("openai", "OpenAI"),
    ("anthropic", "Anthropic Claude"),
]


class CoverLetter(models.Model):
    application = models.ForeignKey(
        Application,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cover_letters",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cover_letters",
    )
    cv_version = models.ForeignKey(
        CVVersion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    content = models.TextField()
    job_description = models.TextField(blank=True)
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    model = models.CharField(max_length=50)
    prompt_settings = models.JSONField(default=dict, blank=True)
    version_number = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Cover Letter for {self.application or 'unlinked'}"


class AIUsageLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ai_usage_logs",
    )
    feature = models.CharField(max_length=20, choices=FEATURE_CHOICES)
    provider = models.CharField(max_length=20)
    model = models.CharField(max_length=50)
    input_tokens = models.IntegerField(default=0)
    output_tokens = models.IntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["user", "feature", "timestamp"]),
        ]

    def __str__(self):
        return f"{self.feature} by {self.user.email} ({self.provider})"
