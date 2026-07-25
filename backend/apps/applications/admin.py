from django.contrib import admin

from .models import Application, ApplicationActivity, CVVersion, Tag


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = [
        "company",
        "role",
        "status",
        "priority",
        "job_type",
        "applied_date",
        "created_at",
    ]
    list_filter = ["status", "job_type", "priority", "is_remote", "source"]
    search_fields = ["company", "role", "location"]
    date_hierarchy = "created_at"
    raw_id_fields = ["user"]


@admin.register(ApplicationActivity)
class ApplicationActivityAdmin(admin.ModelAdmin):
    list_display = ["application", "event_type", "old_value", "new_value", "timestamp"]
    list_filter = ["event_type"]
    readonly_fields = [
        "application",
        "event_type",
        "old_value",
        "new_value",
        "timestamp",
    ]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name", "user", "color"]
    list_filter = ["user"]


@admin.register(CVVersion)
class CVVersionAdmin(admin.ModelAdmin):
    list_display = ["name", "user", "is_default", "created_at"]
    list_filter = ["is_default"]
