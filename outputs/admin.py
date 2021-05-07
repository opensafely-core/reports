from django.contrib import admin

from .models import Output


@admin.register(Output)
class OutputAdmin(admin.ModelAdmin):

    fieldsets = (
        ("Navigation", {"fields": ["menu_name"]}),
        (
            "Output file details",
            {"fields": ["repo", "branch", "output_html_file_path"]},
        ),
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
    readonly_fields = ["last_updated"]
