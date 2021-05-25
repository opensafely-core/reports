import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from model_bakery import baker

from outputs.models import Report


@pytest.mark.django_db
def test_admin_update_cache_action(client):
    """Test the update_cache admin action refreshes the cache_token for selected reports"""
    get_user_model().objects.create_superuser("admin", "admin@test.com", "test")
    report1 = baker.make(Report, menu_name="test")
    report2 = baker.make(Report, menu_name="test")

    report1_cache_token = report1.cache_token
    report2_cache_token = report2.cache_token

    data = {"action": "update_cache", "_selected_action": [report1.id]}
    change_url = reverse("admin:outputs_report_changelist")
    client.login(username="admin", password="test")
    client.post(change_url, data)

    report1.refresh_from_db()
    report2.refresh_from_db()
    assert report1.cache_token != report1_cache_token
    assert report2.cache_token == report2_cache_token
