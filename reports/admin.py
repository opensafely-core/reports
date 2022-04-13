from hashlib import shake_256

from django.contrib import admin, messages
from django.utils.safestring import mark_safe
from django.utils.translation import ngettext

from .models import Category, Link, Report


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    fields = ("name",)


class LinkInline(admin.TabularInline):
    model = Link
    fields = ("icon", "label", "url")


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    inlines = (LinkInline,)
    actions = ["update_cache"]
    fieldsets = (
        ("Navigation", {"fields": ["menu_name", "category"]}),
        (
            "Report file details (GitHub)",
            {
                "description": (
                    "A report file can be hosted on either GitHub or the Jobs site, "
                    "fill in the fields in this section if your file is hosted on GitHub."
                ),
                "fields": ["repo", "branch", "report_html_file_path"],
            },
        ),
        (
            "Report file details (Jobs site)",
            {
                "description": (
                    "A report file can be hosted on either GitHub or the Jobs site, "
                    "paste the direct URL to your HTML output on the Jobs site."
                ),
                "fields": ["job_server_url"],
            },
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
                    "contact_email",
                ]
            },
        ),
        (
            "DOI",
            {
                "fields": [
                    "doi_suffix",
                    "doi",
                ],
                "description": mark_safe(
                    "DOI for the published report.  Note that DOIs must link to a publicly accessible "
                    "landing page, so DOIs can only be entered when the report is published.  Go to "
                    "<a href='https://crossref.org'>crossref.org</a> to register the DOI for this report, "
                    "using the generated DOI suffix below."
                ),
            },
        ),
        ("Visibility", {"fields": ["is_draft"]}),
    )
    readonly_fields = ["last_updated", "cache_token", "doi_suffix"]

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

    def doi_suffix(self, obj):
        """
        Display a suggested DOI to use, based on the report slug
        """
        if obj:
            return f"rpt.{shake_256(obj.slug.encode()).hexdigest(5)}"
        else:
            return "Save to generate DOI suffix"

    doi_suffix.short_description = "Generated DOI suffix"
