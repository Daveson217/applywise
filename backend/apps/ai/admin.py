from django.contrib import admin

from .models import AIUsageLog, CoverLetter


@admin.register(CoverLetter)
class CoverLetterAdmin(admin.ModelAdmin):
    list_display = ["user", "application", "provider", "model", "created_at"]
    list_filter = ["provider"]


@admin.register(AIUsageLog)
class AIUsageLogAdmin(admin.ModelAdmin):
    list_display = ["user", "feature", "provider", "model", "input_tokens", "output_tokens", "timestamp"]
    list_filter = ["feature", "provider"]
