import pytest
from django.core.exceptions import ValidationError
from model_bakery import baker

from outputs.models import Output


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
            {"output_html_file_path": "test-outputs/bad-output.html"},
            False,
            "['File could not be found (branch master)']",
        ),
        (
            {"output_html_file_path": "dummy-outputs/output.html"},
            False,
            "Error fetching output file: Not Found",
        ),
        (
            {"branch": "non-existent-branch"},
            False,
            "Error fetching output file: No commit found for the ref non-existent-branch",
        ),
        (
            {"output_html_file_path": "project.yaml"},
            False,
            "project.yaml must be an html file",
        ),
    ],
    ids=[
        "Test valid",
        "Test non-existent repo",
        "Test non-existent output file",
        "Test non-existent output file and parent path",
        "Test non-existent branch",
        "Test existing but non-html file path",
    ],
)
def test_output_model_validation(fields, expected_valid, expected_errors):
    """Fetch and extract html from a real repo"""
    defaults = {
        "menu_name": "test",
        "repo": "output-explorer-test-repo",
        "branch": "master",
        "output_html_file_path": "test-outputs/output.html",
    }
    output_fields = {**defaults, **fields}
    output = baker.make(Output, **output_fields)
    if not expected_valid:
        with pytest.raises(ValidationError, match=expected_errors):
            output.full_clean()
    else:
        output.full_clean()
