from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin


User = get_user_model()


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        (None, {"fields": ("title", "display_name")}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (
            None,
            {
                "fields": (
                    "title",
                    "display_name",
                )
            },
        ),
    )
