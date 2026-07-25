from django.conf import settings
from django.db import models

RELATIONSHIP_CHOICES = [
    ("recruiter", "Recruiter"),
    ("referral", "Referral"),
    ("peer", "Peer"),
    ("mentor", "Mentor"),
    ("alumni", "Alumni"),
    ("manager", "Hiring Manager"),
    ("other", "Other"),
]

INTERACTION_TYPE_CHOICES = [
    ("coffee_chat", "Coffee Chat"),
    ("email", "Email"),
    ("call", "Phone Call"),
    ("referral", "Referral Submitted"),
    ("interview_prep", "Interview Prep"),
    ("follow_up", "Follow Up"),
    ("linkedin", "LinkedIn Message"),
    ("other", "Other"),
]


class Contact(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="contacts",
    )
    name = models.CharField(max_length=255)
    company = models.CharField(max_length=255, blank=True)
    role = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    linkedin_url = models.URLField(blank=True)
    relationship_type = models.CharField(
        max_length=20, choices=RELATIONSHIP_CHOICES, default="other"
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.company})"


class Interaction(models.Model):
    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        related_name="interactions",
    )
    type = models.CharField(max_length=20, choices=INTERACTION_TYPE_CHOICES)
    date = models.DateField()
    notes = models.TextField(blank=True)
    linked_application = models.ForeignKey(
        "applications.Application",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="interactions",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.get_type_display()} with {self.contact.name} on {self.date}"
