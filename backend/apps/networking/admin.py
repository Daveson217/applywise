from django.contrib import admin

from .models import Contact, Interaction


class InteractionInline(admin.TabularInline):
    model = Interaction
    extra = 0


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ["name", "company", "role", "relationship_type", "user"]
    list_filter = ["relationship_type"]
    search_fields = ["name", "company"]
    inlines = [InteractionInline]


@admin.register(Interaction)
class InteractionAdmin(admin.ModelAdmin):
    list_display = ["contact", "type", "date"]
    list_filter = ["type"]
