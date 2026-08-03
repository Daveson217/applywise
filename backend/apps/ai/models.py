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


class AIGeneration(models.Model):
    """History of Q&A / fit-score / ATS-score outputs so users can revisit
    past results. Cover letters have their own dedicated model — this is
    for the shorter, structured JSON features."""

    HISTORY_FEATURES = [
        ("qa", "Question Answer"),
        ("fit_score", "Fit Score"),
        ("ats_score", "ATS Score"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ai_generations",
    )
    feature = models.CharField(max_length=20, choices=HISTORY_FEATURES)
    # Human-readable one-line label for list views (job title, question preview, etc.)
    title = models.CharField(max_length=255, blank=True)
    # The prompt inputs we sent (so the user can see what they asked)
    input = models.JSONField(default=dict, blank=True)
    # The parsed result the LLM returned
    result = models.JSONField(default=dict, blank=True)
    provider = models.CharField(max_length=20, blank=True)
    model = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["user", "feature", "-created_at"],
                name="ai_gen_user_feat_created_idx",
            ),
        ]

    def __str__(self):
        return f"{self.feature}: {self.title or '(untitled)'}"
