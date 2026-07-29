from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import CustomUserManager

THEME_CHOICES = [
    ("light", "Light"),
    ("dark", "Dark"),
    ("system", "System"),
]

ACCENT_COLOR_CHOICES = [
    ("blue", "Blue"),
    ("teal", "Teal"),
    ("violet", "Violet"),
    ("rose", "Rose"),
    ("amber", "Amber"),
    ("slate", "Slate"),
]

PROVIDER_CHOICES = [
    ("gemini", "Google Gemini"),
    ("openai", "OpenAI"),
    ("anthropic", "Anthropic Claude"),
]


class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    is_email_verified = models.BooleanField(default=False)

    # Password reset — a SHA-256 hash of the currently-outstanding reset
    # token. We store the hash (not the token) so a DB leak doesn't let an
    # attacker mint valid resets. Field is cleared after successful reset,
    # enforcing single-use.
    password_reset_token_hash = models.CharField(max_length=64, blank=True, default="")
    password_reset_requested_at = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = CustomUserManager()

    def __str__(self):
        return self.email


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    phone = models.CharField(max_length=20, blank=True)
    phone_verified = models.BooleanField(default=False)
    graduation_date = models.DateField(null=True, blank=True)
    university = models.CharField(max_length=255, blank=True)
    target_roles = models.JSONField(default=list, blank=True)
    excluded_keywords = models.JSONField(default=list, blank=True)
    target_job_types = models.JSONField(default=list, blank=True)
    preferred_locations = models.JSONField(default=list, blank=True)
    linkedin_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    website_url = models.URLField(blank=True)
    bio = models.TextField(blank=True)
    weekly_goal = models.IntegerField(default=10)
    theme = models.CharField(max_length=10, choices=THEME_CHOICES, default="system")
    accent_color = models.CharField(max_length=10, choices=ACCENT_COLOR_CHOICES, default="blue")
    default_llm_provider = models.CharField(
        max_length=20, choices=PROVIDER_CHOICES, default="gemini"
    )
    default_llm_model = models.CharField(max_length=50, default="gemini-2.5-flash")
    onboarding_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"Profile: {self.user.email}"
