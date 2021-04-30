from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Organisation, Output


User = get_user_model()


class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        (None, {"fields": ("title", "display_name", "organisations")}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (
            None,
            {
                "fields": (
                    "title",
                    "display_name",
                    "organisations",
                )
            },
        ),
    )


class OutputAdmin(admin.ModelAdmin):
    fields = ["menu_name", "repo", "branch", "output_html_file_path"]


# Re-register UserAdmin
admin.site.register(User, UserAdmin)
admin.site.register(Organisation)
admin.site.register(Output, OutputAdmin)
