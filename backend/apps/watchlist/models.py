from django.conf import settings
from django.db import models

ATS_CHOICES = [
    ("greenhouse", "Greenhouse"),
    ("lever", "Lever"),
    ("ashby", "Ashby"),
    ("workable", "Workable"),
    ("smartrecruiters", "SmartRecruiters"),
    ("jsearch", "JSearch"),
    ("manual", "Manual"),
]

SCRAPE_STATUS_CHOICES = [
    ("active", "Active"),
    ("paused", "Paused"),
    ("error", "Error"),
    ("detecting", "Detecting"),
]


class WatchlistCompany(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="watchlist_companies",
    )
    name = models.CharField(max_length=255)
    careers_url = models.URLField(blank=True)
    ats_provider = models.CharField(
        max_length=20, choices=ATS_CHOICES, blank=True
    )
    ats_company_slug = models.CharField(max_length=255, blank=True)
    scrape_status = models.CharField(
        max_length=20, choices=SCRAPE_STATUS_CHOICES, default="active"
    )
    last_checked_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)
    consecutive_failures = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Watchlist companies"

    def __str__(self):
        return f"{self.name} ({self.ats_provider or 'unknown'})"


class WatchlistRule(models.Model):
    company = models.ForeignKey(
        WatchlistCompany,
        on_delete=models.CASCADE,
        related_name="rules",
    )
    keywords = models.JSONField(default=list)
    locations = models.JSONField(default=list)
    job_types = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Rule for {self.company.name}: {self.keywords}"


class JobPosting(models.Model):
    company = models.ForeignKey(
        WatchlistCompany,
        on_delete=models.CASCADE,
        related_name="postings",
    )
    external_id = models.CharField(max_length=255)
    title = models.CharField(max_length=500)
    url = models.URLField(max_length=1000)
    description_text = models.TextField(blank=True)
    location = models.CharField(max_length=255, blank=True)
    first_seen_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_reposted = models.BooleanField(default=False)
    matched_rules = models.BooleanField(default=False)

    class Meta:
        unique_together = [("company", "external_id")]
        ordering = ["-first_seen_at"]

    def __str__(self):
        return f"{self.title} @ {self.company.name}"
