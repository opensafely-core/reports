import datetime
from os import environ

import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
from model_bakery import baker

from reports.models import Category, Report


REAL_REPO_DETAILS = {
    "repo": "output-explorer-test-repo",
    "branch": "master",
    "report_html_file_path": "test-outputs/output.html",
}


@pytest.mark.django_db
@pytest.mark.parametrize(
    "fields,expected_valid,expected_errors",
    [
        ({}, True, None),
        (
            {"repo": "non-existent-repo"},
            False,
            "'non-existent-repo' could not be found",
        ),
        (
            {"report_html_file_path": "test-outputs/bad-report.html"},
            False,
            "['File could not be found (branch master)']",
        ),
        (
            {"report_html_file_path": "dummy-reports/report.html"},
            False,
            "Error fetching report file: Not Found",
        ),
        (
            {"branch": "non-existent-branch"},
            False,
            "Error fetching report file: No commit found for the ref non-existent-branch",
        ),
        (
            {"report_html_file_path": "project.yaml"},
            False,
            "project.yaml must be an html file",
        ),
    ],
    ids=[
        "Test valid",
        "Test non-existent repo",
        "Test non-existent report file",
        "Test non-existent report file and parent path",
        "Test non-existent branch",
        "Test existing but non-html file path",
    ],
)
def test_report_model_validation(fields, expected_valid, expected_errors):
    """Fetch and extract html from a real repo"""
    report_fields = {**REAL_REPO_DETAILS, **fields}
    report = baker.make(Report, **report_fields)
    if not expected_valid:
        with pytest.raises(ValidationError, match=expected_errors):
            report.full_clean()
    else:
        report.full_clean()


@pytest.mark.django_db
def test_category_manager():
    # one category exists already, from the migrations.
    category = Category.objects.first()
    # Create a second category; neither have any associated Reports
    baker.make(Category, name="test")

    # No populated categories
    assert Category.populated.exists() is False

    baker.make(Report, category=category)
    # 2 category objects, only one populated
    assert Category.objects.count() == 2
    assert Category.populated.count() == 1
    assert Category.populated.first() == category


@pytest.mark.django_db
def test_category_for_user(user_no_permission, user_with_permission):
    category = Category.objects.first()
    draft_category = baker.make(Category, name="test")
    baker.make(Report, category=category)
    baker.make(Report, category=draft_category, is_draft=True)

    user = AnonymousUser()
    assert list(Category.populated.for_user(user)) == list(
        Category.objects.filter(id=category.id)
    )
    assert list(Category.populated.for_user(user_no_permission)) == list(
        Category.objects.filter(id=category.id)
    )
    assert list(Category.populated.for_user(user_with_permission)) == list(
        Category.populated.all()
    )


@pytest.mark.django_db
def test_report_menu_name_autopopulates():
    category = baker.make(Category, name="test")
    report = Report(
        title="Fungible watermelon",
        category=category,
        publication_date=datetime.date.today(),
        description="A description",
        **REAL_REPO_DETAILS
    )
    report.full_clean()
    assert report.menu_name == "Fungible watermelon"


@pytest.mark.django_db
def test_report_menu_name_is_limited_to_sixty_characters():
    category = baker.make(Category, name="test")
    report = Report(
        title="012345678901234567890123456789012345678901234567890123456789X",
        category=category,
        publication_date=datetime.date.today(),
        description="A description",
        **REAL_REPO_DETAILS
    )
    with pytest.raises(ValidationError, match="at most 60 characters"):
        report.full_clean()


@pytest.mark.parametrize(
    "update_fields,cache_token_changed,logs_exist,last_log",
    [
        ({}, False, False, None),
        (
            {"description": "new"},
            True,
            True,
            "Non-repo field(s) updated; refreshing cache token only",
        ),
        ({"is_draft": False}, False, False, None),
        (
            {"report_html_file_path": "foo.html"},
            True,
            True,
            "Source repo field(s) updated; refreshing cache token and clearing requests cache",
        ),
    ],
    ids=[
        "no updates",
        "non-repo field updated",
        "irrelevant field updated",
        "repo field updated",
    ],
)
@pytest.mark.django_db
def test_cache_refresh_on_report_save(
    reset_environment_after_test,
    log_output,
    update_fields,
    cache_token_changed,
    logs_exist,
    last_log,
):
    environ["GITHUB_VALIDATION"] = "False"
    report = baker.make(
        Report,
        category=Category.objects.first(),
        title="test",
        report_html_file_path="test.html",
        is_draft=False,
    )
    report.save()
    report_id = report.id
    initial_cache_token = report.cache_token
    # No cache logs on initial save
    assert log_output.entries == []

    # Fetch from the db again so the initial values are registered
    report = Report.objects.get(id=report_id)
    # update fields and save
    for field, value in update_fields.items():
        setattr(report, field, value)
    report.save()
    if logs_exist:
        assert log_output.entries[-1]["event"] == last_log
    else:
        assert log_output.entries == []
    assert (initial_cache_token != report.cache_token) == cache_token_changed
    log_output.entries.clear()
