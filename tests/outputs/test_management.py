import pytest
from django.contrib.auth import get_user_model
from django.core import management

from outputs.models import Output


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
def test_populate_outputs():
    assert Output.objects.exists() is False
    management.call_command("populate_outputs")

    assert Output.objects.count() == 1
    assert Output.objects.first().title == "Vaccine Coverage"

    # calling it again does nothing
    management.call_command("populate_outputs")
    assert Output.objects.count() == 1
