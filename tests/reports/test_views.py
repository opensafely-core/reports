from datetime import date, timedelta

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from reports.groups import setup_researchers
from reports.models import Category, Report
from reports.rendering import process_html

from ..factories import CategoryFactory, ReportFactory, UserFactory
from .utils import assert_html_equal


User = get_user_model()


@pytest.mark.django_db
def test_landing_view(client, mock_repo_url, bennett_org):
    """Test landing view context"""
    mock_repo_url("https://github.com/opensafely/test-repo")

    assert Report.objects.exists() is False
    # By default we have one Category, set up in the migration
    assert Category.objects.count() == 1
    response = client.get(reverse("landing"))

    # There is a category, but it isn't included in the context because it has no associated Reports
    assert list(response.context["categories"]) == []

    # when Reports exist, their categories are included in the context
    report1 = ReportFactory(org=bennett_org)
    report2 = ReportFactory(org=bennett_org, title="test1")
    response = client.get(reverse("landing"))
    assert list(response.context["categories"]) == [report1.category, report2.category]


@pytest.mark.django_db
def test_landing_view_ordering(client, mock_repo_url, bennett_org):
    """Test categories and reports in context are alphabetically ordered"""
    mock_repo_url("https://github.com/opensafely/test-repo")

    # By default we have one Category, set up in the migration
    assert Category.objects.count() == 1
    reports_category = Category.objects.first()
    assert reports_category.name == "Reports"

    # make another category and add some reports
    test_category = CategoryFactory(name="Test")

    ReportFactory(category=test_category, org=bennett_org, menu_name="xyz")
    ReportFactory(category=test_category, org=bennett_org, menu_name="abc")
    ReportFactory(category=test_category, org=bennett_org, menu_name="def")
    ReportFactory(category=reports_category, org=bennett_org, menu_name="jkl")
    ReportFactory(category=reports_category, org=bennett_org, menu_name="bcd")

    response = client.get(reverse("landing"))
    # Categories are in alphabetical order by name
    assert list(response.context["categories"].values_list("name", flat=True)) == [
        "Reports",
        "Test",
    ]
    # Within each category, reports are in alphabetical order by menu_name
    reports_category_context, test_category_context = response.context["categories"]
    assert list(
        reports_category_context.reports.values_list("menu_name", flat=True)
    ) == ["bcd", "jkl"]
    assert list(test_category_context.reports.values_list("menu_name", flat=True)) == [
        "abc",
        "def",
        "xyz",
    ]


@pytest.mark.parametrize(
    "user_attributes,expected_category_names,expected_report_names",
    [
        (None, ["Reports"], {"report-abc", "report-def"}),
        ("no_permission", ["Reports"], {"report-abc", "report-def"}),
        (
            "has_permission",
            ["Reports", "Test"],
            {"report-abc", "report-def", "report-ghi", "report-jkl", "report-mno"},
        ),
    ],
)
@pytest.mark.django_db
def test_landing_view_draft_reports_permissions(
    client,
    mock_repo_url,
    user_with_permission,
    user_attributes,
    expected_category_names,
    expected_report_names,
    bennett_org,
):
    mock_repo_url("https://github.com/opensafely/test-repo")
    user_selection = {
        "no_permission": UserFactory(),
        "has_permission": user_with_permission,
    }
    user = user_selection.get(user_attributes)
    if user is not None:
        client.force_login(user)

    # By default we have one Category, set up in the migration
    assert Category.objects.count() == 1
    reports_category = Category.objects.first()
    assert reports_category.name == "Reports"
    # add some draft and published reports
    report1 = ReportFactory(org=bennett_org, menu_name="report-abc")
    report2 = ReportFactory(org=bennett_org, menu_name="report-def")
    report3 = ReportFactory(org=bennett_org, menu_name="report-ghi", is_draft=True)
    reports_category.reports.add(report1, report2, report3)

    # make another category and add draft reports ONLY.
    # This entire category should be hidden from an anonymous user and a user with no permission
    draft_category = CategoryFactory(name="Test")
    ReportFactory(
        category=draft_category, org=bennett_org, menu_name="report-jkl", is_draft=True
    )
    ReportFactory(
        category=draft_category, org=bennett_org, menu_name="report-mno", is_draft=True
    )

    response = client.get(reverse("landing"))
    assert response.context["categories"].count() == len(expected_category_names)
    categories = response.context["categories"]
    assert [category.name for category in categories] == expected_category_names

    all_report_names = {
        "report-abc",
        "report-def",
        "report-ghi",
        "report-jkl",
        "report-mno",
    }
    content = response.content.decode("utf-8")
    for report_name in expected_report_names:
        assert report_name in content
    for report_name in all_report_names - expected_report_names:
        assert report_name not in content


@pytest.mark.django_db
@pytest.mark.parametrize(
    "reports,expected",
    [
        (
            {
                "test1": {"publication_date": date(2021, 2, 1)},
                "test2": {"publication_date": date(2021, 1, 1)},
                "test3": {"publication_date": date(2021, 3, 1)},
            },
            [
                ("test3", "published", date(2021, 3, 1)),
                ("test1", "published", date(2021, 2, 1)),
                ("test2", "published", date(2021, 1, 1)),
            ],
        ),
        (
            {
                "test1": {"publication_date": date(2021, 2, 1)},
                "test2": {
                    "publication_date": date(2021, 1, 1),
                    "last_updated": date(2021, 1, 1),
                },
            },
            [
                ("test1", "published", date(2021, 2, 1)),
                ("test2", "published", date(2021, 1, 1)),
            ],
        ),
        (
            {
                "test1": {"publication_date": date(2021, 2, 1)},
                "test2": {
                    "publication_date": date(2021, 1, 1),
                    "last_updated": date(2021, 3, 1),
                },
            },
            [
                ("test2", "updated", date(2021, 3, 1)),
                ("test1", "published", date(2021, 2, 1)),
            ],
        ),
        (
            # setup 12 reports published on 1st, 2nd, ...12th
            {
                f"test{i}": {"publication_date": date(2021, 1, 1) + timedelta(days=i)}
                for i in range(12)
            },
            # expect 11 reports published on 10th, 9th, ...1st
            [
                (
                    f"test{11 - i}",
                    "published",
                    date(2021, 1, 1) + timedelta(days=(11 - i)),
                )
                for i in range(10)
            ],
        ),
    ],
    ids=[
        "Orders reports by publication date, most recent first",
        "Only mentions publication if a report is updated the same day it's published",
        "Only mentions update if a report is updated after publication",
        "Only 10 most recent events are shown",
    ],
)
def test_landing_view_recent_activity(
    client, mock_repo_url, bennett_org, reports, expected
):
    mock_repo_url("https://github.com/opensafely/test-repo")

    for menu_name, report_fields in reports.items():
        ReportFactory(org=bennett_org, menu_name=menu_name, **report_fields)

    response = client.get(reverse("landing"))
    # only reports with dates are shown in recent_activity
    # report activity is returned in reverse date order
    # reports have additional annotation fields "activity" and "activity_date"
    context_report = [
        (report.menu_name, report.activity, report.activity_date)
        for report in response.context["recent_activity"]
    ]
    assert context_report == expected


@pytest.mark.django_db
def test_landing_view_recent_activity_archived_reports(
    client, bennett_org, mock_repo_url
):
    """Archived reports do not appear in recent activity unless user is staff"""
    mock_repo_url("https://github.com/opensafely/test-repo")

    report = ReportFactory(
        org=bennett_org, menu_name="test", publication_date="2021-02-01"
    )
    # report is not archived, appears in recent activity
    response = client.get(reverse("landing"))
    assert list(response.context["recent_activity"]) == [report]

    # archived report
    category = CategoryFactory(name="Archive")
    report.category = category
    report.save()

    response = client.get(reverse("landing"))
    assert list(response.context["recent_activity"]) == []


@pytest.mark.django_db
def test_login_get(client):
    response = client.get(reverse("login"))

    assert response.status_code == 200


@pytest.mark.django_db
def test_login_post(client):
    user = User.objects.create(username="test")
    user.set_password("test")

    response = client.post(
        reverse("login"),
        {"username": "test", "password": "test"},
        follow=True,
    )

    assert response.status_code == 200
    assert response.redirect_chain == []


@pytest.mark.django_db
def test_report_view(client, bennett_org):
    """Test a single report page"""
    # report for a real file
    report = ReportFactory(
        org=bennett_org,
        title="test",
        repo="output-explorer-test-repo",
        branch="master",
        report_html_file_path="test-outputs/output.html",
    )
    response = client.get(report.get_absolute_url())

    assert_html_equal(
        process_html(response.context["remote"].get_html()),
        """
            <h1>A Test Output HTML file</h1>
            <p>The test content</p>
        """,
    )


@pytest.mark.django_db
def test_archive_report_view(client, bennett_org):
    """Test that an archive report is accessible, but not listed in categories"""
    category = Category.objects.first()
    ReportFactory(
        category=category,
        org=bennett_org,
        title="test",
        repo="output-explorer-test-repo",
        branch="master",
        report_html_file_path="test-outputs/output.html",
    )
    archive_report = ReportFactory(
        category=CategoryFactory(name="Archive"),
        org=bennett_org,
        title="test",
        repo="output-explorer-test-repo",
        branch="master",
        report_html_file_path="test-outputs/output.html",
    )

    response = client.get(archive_report.get_absolute_url())
    assert response.status_code == 200
    assert response.context["report"] == archive_report
    assert [category.id for category in response.context["categories"]] == [category.id]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_attributes,is_draft,expected_status",
    [
        (None, False, 200),
        (None, True, 404),
        ("no_permission", False, 200),
        ("no_permission", True, 404),
        ("has_permission", False, 200),
        ("has_permission", True, 200),
        ("researcher", False, 200),
        ("researcher", True, 200),
    ],
)
def test_draft_report_view_permissions(
    client,
    user_with_permission,
    bennett_org,
    user_attributes,
    is_draft,
    expected_status,
):
    """Test a single report page"""
    # report for a real file
    report = ReportFactory(
        org=bennett_org,
        title="test",
        repo="output-explorer-test-repo",
        branch="master",
        report_html_file_path="test-outputs/output.html",
        is_draft=is_draft,
    )

    # set up a researcher user with the approrpriate group
    group = setup_researchers()
    researcher = UserFactory(username="researcher")
    researcher.groups.add(group)
    user_selection = {
        "no_permission": UserFactory(),
        "has_permission": user_with_permission,
        "researcher": researcher,
    }
    user = user_selection.get(user_attributes)
    if user is not None:
        client.force_login(user)

    response = client.get(report.get_absolute_url())
    assert response.status_code == expected_status


def assert_last_cache_log(log_entries, expected_log_items):
    last_cache_log = next(
        (
            log
            for log in reversed(log_entries.entries)
            if "cache" in log["event"].lower()
        ),
        None,
    )
    if expected_log_items is None:
        assert last_cache_log is None
    else:
        for key, value in expected_log_items.items():
            assert last_cache_log[key] == value
    log_entries.entries.clear()


@pytest.mark.django_db
def test_report_view_cache(client, log_output, bennett_org):
    """
    Test caching a single report page.
    """
    report = ReportFactory(
        org=bennett_org,
        title="test",
        repo="output-explorer-test-repo",
        branch="master",
        report_html_file_path="test-outputs/output.html",
    )

    # fetch report
    response = client.get(report.get_absolute_url())
    assert response.status_code == 200

    # force update
    response = client.get(report.get_absolute_url() + "?force-update=")
    old_token = report.cache_token
    report.refresh_from_db()
    assert old_token != report.cache_token
    assert_last_cache_log(
        log_output,
        {
            "report_id": report.id,
            "slug": report.slug,
            "event": "Cache token refreshed and requests cache cleared; redirecting...",
        },
    )
    assert response.status_code == 302
    assert response.url == report.get_absolute_url()


@pytest.mark.django_db
def test_report_view_last_updated(client, log_output, bennett_org):
    """
    Test that the last updated field (which is fetched on page load and stored on the
    model) is displayed properly on the report page.
    """
    report = ReportFactory(
        org=bennett_org,
        title="test",
        repo="output-explorer-test-repo",
        branch="master",
        report_html_file_path="test-outputs/output.html",
    )
    assert report.last_updated is None

    # fetch report
    response = client.get(report.get_absolute_url())
    assert response.status_code == 200

    report.refresh_from_db()
    assert report.last_updated is not None
    assert report.last_updated.strftime("%d %b %Y") in response.rendered_content
