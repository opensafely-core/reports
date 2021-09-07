from hashlib import shake_256

import pytest
from django.contrib.admin import AdminSite
from django.contrib.auth import get_user_model
from django.urls import reverse
from model_bakery import baker

from reports.admin import ReportAdmin
from reports.models import Report


@pytest.mark.django_db
def test_admin_update_cache_action(client, mock_repo_url):
    """Test the update_cache admin action refreshes the cache_token for selected reports"""
    mock_repo_url("http://github.com/opensafely/test-repo")
    get_user_model().objects.create_superuser("admin", "admin@test.com", "test")
    report1 = baker.make_recipe("reports.dummy_report", title="test")
    report2 = baker.make_recipe("reports.dummy_report", title="test")

    report1_cache_token = report1.cache_token
    report2_cache_token = report2.cache_token

    data = {"action": "update_cache", "_selected_action": [report1.id]}
    change_url = reverse("admin:reports_report_changelist")
    client.login(username="admin", password="test")
    client.post(change_url, data)

    report1.refresh_from_db()
    report2.refresh_from_db()
    assert report1.cache_token != report1_cache_token
    assert report2.cache_token == report2_cache_token


@pytest.mark.django_db
def test_admin_doi_suffix(client, mock_repo_url):
    mock_repo_url("http://github.com/opensafely/test-repo")
    get_user_model().objects.create_superuser("admin", "admin@test.com", "test")
    report_admin = ReportAdmin(Report, AdminSite())

    report = baker.make_recipe("reports.dummy_report", title="test")
    assert (
        report_admin.doi_suffix(report)
        == f"rpt.{shake_256(report.slug.encode()).hexdigest(5)}"
    )

    # A second report with the same name gets a different slug and therefore different DOI suffix
    report1 = baker.make_recipe("reports.dummy_report", title="test")
    assert report1.slug != report.slug
    assert report_admin.doi_suffix(report) != report_admin.doi_suffix(report1)
