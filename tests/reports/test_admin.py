from hashlib import shake_256

import pytest
from django.contrib.admin import AdminSite
from django.urls import reverse

from reports.admin import IsExternalFilter, ReportAdmin
from reports.models import Report

from ..factories import ReportFactory, UserFactory


@pytest.mark.django_db
def test_admin_update_cache_action(client, bennett_org, mock_repo_url):
    """Test the update_cache admin action refreshes the cache_token for selected reports"""
    mock_repo_url("http://github.com/opensafely/test-repo")

    admin = UserFactory(username="admin", is_staff=True, is_superuser=True)
    report1 = ReportFactory(org=bennett_org, title="test")
    report2 = ReportFactory(org=bennett_org, title="test")

    report1_cache_token = report1.cache_token
    report2_cache_token = report2.cache_token

    data = {"action": "update_cache", "_selected_action": [report1.id]}
    client.force_login(admin)

    response = client.post(reverse("admin:reports_report_changelist"), data)

    assert response.status_code == 302

    report1.refresh_from_db()
    report2.refresh_from_db()
    assert report1.cache_token != report1_cache_token
    assert report2.cache_token == report2_cache_token


@pytest.mark.django_db
def test_admin_doi_suffix(client, bennett_org, mock_repo_url):
    mock_repo_url("http://github.com/opensafely/test-repo")

    report = ReportFactory(org=bennett_org, title="test")

    report_admin = ReportAdmin(Report, AdminSite())
    assert (
        report_admin.doi_suffix(report)
        == f"rpt.{shake_256(report.slug.encode()).hexdigest(5)}"
    )

    # A second report with the same name gets a different slug and therefore different DOI suffix
    report1 = ReportFactory(org=bennett_org, title="test")
    assert report1.slug != report.slug
    assert report_admin.doi_suffix(report) != report_admin.doi_suffix(report1)


@pytest.mark.django_db
def test_isexternalfilter(rf, bennett_org):
    report1 = ReportFactory(org=bennett_org)
    report2 = ReportFactory(external_description="test")

    request = rf.get("/")
    report_admin = ReportAdmin(Report, AdminSite())

    qs = Report.objects.all()

    # no
    f = IsExternalFilter(request, {"is_external": "no"}, Report, report_admin)
    assert list(f.queryset(request, qs)) == [report1]

    # yes
    f = IsExternalFilter(request, {"is_external": "yes"}, Report, report_admin)
    assert list(f.queryset(request, qs)) == [report2]
