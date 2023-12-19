from hashlib import shake_256

from django.contrib import admin, messages
from django.utils.safestring import mark_safe
from django.utils.translation import ngettext

from .models import Category, Link, Org, Report


class HostingFilter(admin.SimpleListFilter):
    parameter_name = "hosted_on"
    title = "hosting location"

    def lookups(self, request, model_admin):
        return [
            ("github", "GitHub"),
            ("job-server", "Job Server"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "github":
            return queryset.filter(job_server_url="")

        if self.value() == "job-server":
            return queryset.exclude(job_server_url="")

        return queryset


class IsExternalFilter(admin.SimpleListFilter):
    parameter_name = "is_external"
    title = "is external"

    def lookups(self, request, model_admin):
        return [
            ("no", "No"),
            ("yes", "Yes"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "no":
            return queryset.filter(org__slug="bennett")

        if self.value() == "yes":
            return queryset.exclude(org__slug="bennett")

        return queryset


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    fields = ("name",)


class LinkInline(admin.TabularInline):
    model = Link
    fields = ("icon", "label", "url")


@admin.register(Org)
class OrgAdmin(admin.ModelAdmin):
    fields = ["name", "slug", "url", "logo"]


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    inlines = (LinkInline,)
    actions = ["update_cache"]
    list_display = ("__str__", "updated_at", "updated_by")
    list_filter = ["org", IsExternalFilter, HostingFilter, "created_by", "updated_by"]
    fieldsets = (
        ("Organisation", {"fields": ["org"]}),
        ("Navigation", {"fields": ["category", "menu_name"]}),
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
        ("External", {"fields": ["external_description"]}),
        (
            "Auditing",
            {"fields": ["created_at", "created_by", "updated_at", "updated_by"]},
        ),
    )
    readonly_fields = [
        "cache_token",
        "created_at",
        "created_by",
        "doi_suffix",
        "last_updated",
        "updated_at",
        "updated_by",
    ]

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

    def doi_suffix(self, obj):  # pragma: no cover
        """
        Display a suggested DOI to use, based on the report slug
        """
        if obj:
            return f"rpt.{shake_256(obj.slug.encode()).hexdigest(5)}"
        else:
            return "Save to generate DOI suffix"

    def save_model(self, request, obj, form, change):
        if obj.created_by_id is None:
            obj.created_by = request.user

        # ensure updated_by is both set on model creation _and_ update
        obj.updated_by = request.user

        super().save_model(request, obj, form, change)

    doi_suffix.short_description = "Generated DOI suffix"
