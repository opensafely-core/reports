import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from model_bakery import baker

from outputs.models import Output


@pytest.mark.django_db
def test_admin_update_cache_action(client):
    """Test the update_cache admin action refreshes the cache_token for selected outputs"""
    get_user_model().objects.create_superuser("admin", "admin@test.com", "test")
    output1 = baker.make(Output, menu_name="test")
    output2 = baker.make(Output, menu_name="test")

    output1_cache_token = output1.cache_token
    output2_cache_token = output2.cache_token

    data = {"action": "update_cache", "_selected_action": [output1.id]}
    change_url = reverse("admin:outputs_output_changelist")
    client.login(username="admin", password="test")
    client.post(change_url, data)

    output1.refresh_from_db()
    output2.refresh_from_db()
    assert output1.cache_token != output1_cache_token
    assert output2.cache_token == output2_cache_token
