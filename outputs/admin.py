from django.contrib import admin

from .models import Output


class OutputAdmin(admin.ModelAdmin):
    fields = ["menu_name", "repo", "branch", "output_html_file_path"]


admin.site.register(Output, OutputAdmin)
