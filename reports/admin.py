from django.contrib import admin, messages
from django.utils.translation import ngettext

from .models import Category, Report


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    fields = ("name",)


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    actions = ["update_cache"]
    fieldsets = (
        ("Navigation", {"fields": ["menu_name", "category"]}),
        (
            "Report file details",
            {"fields": ["repo", "branch", "report_html_file_path"]},
        ),
        ("Caching", {"fields": ["cache_token"]}),
        (
            "Front matter",
            {
                "fields": [
                    "authors",
                    "title",
                    "description",
                    "publication_date",
                    "last_updated",
                ]
            },
        ),
        ("Visibility", {"fields": ["is_draft"]}),
    )
    readonly_fields = ["last_updated", "cache_token"]

    @admin.action(description="Force a cache update")
    def update_cache(self, request, queryset):
        for obj in queryset:
            obj.refresh_cache_token()
        updated = queryset.count()
        self.message_user(
            request,
            ngettext(
                "Cache token refreshed for %d report.",
                "Cache token refreshed for %d reports.",
                updated,
            )
            % updated,
            messages.SUCCESS,
        )
