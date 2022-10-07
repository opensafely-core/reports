from django.contrib.auth.models import Group, Permission


def setup_researchers():
    group, _ = Group.objects.get_or_create(name="researchers")

    # we want to add permissions for all our core objects in the reports app to the researchers group
    required_permissions = Permission.objects.filter(
        content_type__app_label="reports",
        content_type__model__in=["report", "category", "link", "org"],
    )

    # set missing permissions on the group
    group_permissions = group.permissions.all()
    missing_permissions = set(required_permissions) - set(group_permissions)
    for missing_permission in missing_permissions:
        group.permissions.add(missing_permission)

    return group
