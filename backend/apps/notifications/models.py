from django.conf import settings
from django.db import models

NOTIF_TYPE_CHOICES = [
    ("job_alert", "Job Alert"),
    ("reminder", "Reminder"),
    ("ai_suggestion", "AI Suggestion"),
    ("system", "System"),
]


class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    type = models.CharField(max_length=20, choices=NOTIF_TYPE_CHOICES)
    title = models.CharField(max_length=255)
    body = models.TextField()
    link = models.URLField(blank=True)
    # Structured payload for the email task — keeps us from parsing free text
    # (XSS / data-leak safer). Example: {"posting_id": 123}
    metadata = models.JSONField(default=dict, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_read", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.user.email})"
