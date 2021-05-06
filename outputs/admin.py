from django.contrib import admin

from .models import Output


class OutputAdmin(admin.ModelAdmin):
    fields = [
        "menu_name",
        "repo",
        "branch",
        "output_html_file_path",
        "authors",
        "title",
        "description",
        "publication_date",
        "last_updated",
    ]
    readonly_fields = ["last_updated"]


admin.site.register(Output, OutputAdmin)
