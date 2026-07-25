from django.contrib import admin

from .models import JobPosting, WatchlistCompany, WatchlistRule


class WatchlistRuleInline(admin.TabularInline):
    model = WatchlistRule
    extra = 0


@admin.register(WatchlistCompany)
class WatchlistCompanyAdmin(admin.ModelAdmin):
    list_display = ["name", "user", "ats_provider", "scrape_status", "last_checked_at"]
    list_filter = ["ats_provider", "scrape_status"]
    search_fields = ["name"]
    inlines = [WatchlistRuleInline]


@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    list_display = ["title", "company", "location", "is_active", "first_seen_at"]
    list_filter = ["is_active", "is_reposted"]
    search_fields = ["title"]
