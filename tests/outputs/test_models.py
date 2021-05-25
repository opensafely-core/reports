import pytest
from django.core.exceptions import ValidationError
from model_bakery import baker

from outputs.models import Category, Report


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
    defaults = {
        "repo": "output-explorer-test-repo",
        "branch": "master",
        "report_html_file_path": "test-outputs/output.html",
    }
    report_fields = {**defaults, **fields}
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
