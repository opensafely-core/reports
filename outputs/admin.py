from django.contrib import admin, messages
from django.utils.translation import ngettext

from .models import Category, Output


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    fields = ("name",)


@admin.register(Output)
class OutputAdmin(admin.ModelAdmin):
    actions = ["update_cache"]
    fieldsets = (
        ("Navigation", {"fields": ["menu_name"]}),
        (
            "Output file details",
            {"fields": ["repo", "branch", "output_html_file_path"]},
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
                "Cache token refreshed for %d output.",
                "Cache token refreshed for %d outputs.",
                updated,
            )
            % updated,
            messages.SUCCESS,
        )
