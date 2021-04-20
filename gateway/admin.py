from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Organisation

User = get_user_model()


class UserAdmin(BaseUserAdmin):
    ...
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


# Re-register UserAdmin
admin.site.register(User, UserAdmin)
admin.site.register(Organisation)
