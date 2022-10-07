import pytest

from ..factories import UserFactory


@pytest.mark.django_db
def test_user_get_full_name():
    user = UserFactory(display_name="Display Name")
    assert user.get_full_name() == "Display Name"
