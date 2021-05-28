import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core import management

from reports.models import Report


User = get_user_model()


@pytest.mark.django_db
def test_ensure_superuser():
    """ensure_superuser management command creates a new superuser"""
    assert User.objects.exists() is False
    management.call_command("ensure_superuser")

    assert User.objects.count() == 1
    new_user = User.objects.first()
    assert new_user.is_superuser
    assert new_user.username == "admin"
    assert new_user.email == "admin@example.com"


@pytest.mark.django_db
def test_ensure_superuser_with_existing_superuser():
    User.objects.create_superuser(
        username="admin", password="test", email="super@user.test"
    )
    management.call_command("ensure_superuser")

    assert User.objects.count() == 1
    assert User.objects.first().email == "super@user.test"


@pytest.mark.django_db
def test_populate_reports():
    assert Report.objects.exists() is False
    management.call_command("populate_reports")

    assert Report.objects.count() == 1
    assert Report.objects.first().title == "Vaccine Coverage"

    # calling it again does nothing
    management.call_command("populate_reports")
    assert Report.objects.count() == 1


@pytest.mark.django_db
def test_ensure_groups():
    assert Group.objects.exists() is False
    management.call_command("ensure_groups")
    assert Group.objects.count() == 1
    group = Group.objects.first()
    assert group.name == "researchers"

    # researchers group gets all model permissions for the reports app
    permissions = Permission.objects.filter(content_type__app_label="reports")
    for permission in permissions:
        assert permission in group.permissions.all()


@pytest.mark.django_db
def test_ensure_groups_existing_group():
    group = Group.objects.create(name="researchers")
    assert group.permissions.exists() is False
    management.call_command("ensure_groups")
    assert Group.objects.count() == 1
    group.refresh_from_db()

    # missing permissions have been added
    permissions = Permission.objects.filter(content_type__app_label="reports")
    for permission in permissions:
        assert permission in group.permissions.all()
