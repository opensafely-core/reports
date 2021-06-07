from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Ensure the researchers group exists with relevant permissions."

    def handle(self, *args, **options):
        group, _ = Group.objects.get_or_create(name="researchers")
        models = ["report", "category", "link"]
        required_permissions = Permission.objects.filter(
            content_type__app_label="reports", content_type__model__in=models
        )
        group_permissions = group.permissions.all()
        missing_permissions = set(required_permissions) - set(group_permissions)
        for missing_permission in missing_permissions:
            group.permissions.add(missing_permission)
