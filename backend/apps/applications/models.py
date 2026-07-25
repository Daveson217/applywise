from django.conf import settings
from django.db import models

JOB_TYPE_CHOICES = [
    ("internship", "Internship"),
    ("coop", "Co-op"),
    ("fulltime", "Full-time"),
    ("parttime", "Part-time"),
    ("contract", "Contract"),
]

STATUS_CHOICES = [
    ("saved", "Saved"),
    ("applied", "Applied"),
    ("oa_assessment", "OA/Assessment"),
    ("phone_screen", "Phone Screen"),
    ("interview", "Interview"),
    ("final_round", "Final Round"),
    ("offer_received", "Offer Received"),
    ("accepted", "Accepted"),
    ("rejected", "Rejected"),
    ("withdrawn", "Withdrawn"),
    ("ghosted", "Ghosted"),
]

SOURCE_CHOICES = [
    ("linkedin", "LinkedIn"),
    ("handshake", "Handshake"),
    ("indeed", "Indeed"),
    ("direct", "Direct"),
    ("referral", "Referral"),
    ("career_fair", "Career Fair"),
    ("other", "Other"),
]

PRIORITY_CHOICES = [
    ("high", "High"),
    ("medium", "Medium"),
    ("low", "Low"),
]

EVENT_TYPE_CHOICES = [
    ("created", "Created"),
    ("status_change", "Status Change"),
    ("note_added", "Note Added"),
    ("updated", "Updated"),
    ("follow_up_set", "Follow Up Set"),
]


class Tag(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tags",
    )
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default="#3B82F6")

    class Meta:
        unique_together = [("user", "name")]
        ordering = ["name"]

    def __str__(self):
        return self.name


class CVVersion(models.Model):
    """Minimal stub for Phase 1 — full implementation in Phase 2."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cv_versions",
    )
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to="cvs/")
    file_size = models.IntegerField(default=0)
    extracted_text = models.TextField(blank=True)
    parsed_json = models.JSONField(default=dict, blank=True)
    tags = models.JSONField(default=list, blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.user.email})"


class Application(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="applications",
    )
    company = models.CharField(max_length=255)
    role = models.CharField(max_length=255)
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="saved"
    )
    applied_date = models.DateField(null=True, blank=True)
    deadline = models.DateField(null=True, blank=True)
    salary_min = models.IntegerField(null=True, blank=True)
    salary_max = models.IntegerField(null=True, blank=True)
    salary_currency = models.CharField(max_length=3, default="USD")
    location = models.CharField(max_length=255, blank=True)
    is_remote = models.BooleanField(default=False)
    url = models.URLField(blank=True)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, blank=True)
    notes = models.TextField(blank=True)
    priority = models.CharField(
        max_length=10, choices=PRIORITY_CHOICES, default="medium"
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="applications")
    cv_version = models.ForeignKey(
        CVVersion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="applications",
    )
    ai_fit_score = models.IntegerField(null=True, blank=True)
    follow_up_date = models.DateField(null=True, blank=True)
    recruiter_name = models.CharField(max_length=255, blank=True)
    recruiter_email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["user", "created_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(salary_min__isnull=True)
                    | models.Q(salary_max__isnull=True)
                    | models.Q(salary_min__lte=models.F("salary_max"))
                ),
                name="salary_min_lte_max",
            ),
        ]

    def __str__(self):
        return f"{self.company} - {self.role}"


class ApplicationActivity(models.Model):
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="activities",
    )
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES)
    old_value = models.CharField(max_length=255, blank=True)
    new_value = models.CharField(max_length=255, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["application", "timestamp"]),
        ]

    def __str__(self):
        return f"{self.event_type}: {self.application}"
