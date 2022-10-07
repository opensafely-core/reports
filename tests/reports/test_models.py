from os import environ

import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError

from reports.models import Category, Link, Report

from ..factories import CategoryFactory, LinkFactory, ReportFactory, UserFactory


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
        (
            {"doi": "https://doi.test", "is_draft": True},
            False,
            "DOIs cannot be assigned to draft reports",
        ),
        ({"doi": "https://doi.test", "is_draft": False}, True, None),
    ],
    ids=[
        "Test valid",
        "Test non-existent repo",
        "Test non-existent report file",
        "Test non-existent report file and parent path",
        "Test non-existent branch",
        "Test existing but non-html file path",
        "Test DOI with draft report",
        "Test DOI with published report",
    ],
)
def test_report_model_validation(
    bennett_org, fields, expected_valid, expected_errors, reset_environment_after_test
):
    """Fetch and extract html from a real repo"""
    environ["GITHUB_VALIDATION"] = "True"
    report_fields = {**REAL_REPO_DETAILS, **fields}
    if not expected_valid:
        with pytest.raises(ValidationError, match=expected_errors):
            ReportFactory(org=bennett_org, **report_fields)
    else:
        ReportFactory(org=bennett_org, **report_fields)


@pytest.mark.django_db
def test_category_manager(bennett_org):
    # one category exists already, from the migrations.
    category = Category.objects.first()
    # Create a second category; neither have any associated Reports
    CategoryFactory(name="test")

    # No populated categories
    assert Category.populated.exists() is False

    ReportFactory(org=bennett_org, category=category)

    # 2 category objects, only one populated
    assert Category.objects.count() == 2
    assert Category.populated.count() == 1
    assert Category.populated.first() == category


@pytest.mark.django_db
def test_category_for_user(bennett_org, user_with_permission):
    category = CategoryFactory()
    ReportFactory(org=bennett_org, category=category)
    ReportFactory(org=bennett_org, category=CategoryFactory(name="test"), is_draft=True)

    user = AnonymousUser()
    assert list(Category.populated.for_user(user)) == list(
        Category.objects.filter(id=category.id)
    )
    assert list(Category.populated.for_user(UserFactory())) == list(
        Category.objects.filter(id=category.id)
    )
    assert list(Category.populated.for_user(user_with_permission)) == list(
        Category.populated.all()
    )


@pytest.mark.django_db
def test_archive_category_for_user(bennett_org, user_with_permission):
    # Archive category is never returned in the populated_for_user manager
    category = CategoryFactory()
    ReportFactory(org=bennett_org, category=category)
    ReportFactory(org=bennett_org, category=CategoryFactory(name="Archive"))

    user = AnonymousUser()
    assert list(Category.populated.for_user(user)) == list(
        Category.objects.filter(id=category.id)
    )
    assert list(Category.populated.for_user(UserFactory())) == list(
        Category.objects.filter(id=category.id)
    )
    assert list(Category.populated.for_user(user_with_permission)) == list(
        Category.objects.filter(id=category.id)
    )


@pytest.mark.django_db
def test_report_all_github_and_all_job_server_fields_filled(bennett_org):
    try:
        ReportFactory(
            org=bennett_org,
            job_server_url="http://example.com/",
            **REAL_REPO_DETAILS,
        )
    except ValidationError as e:
        assert (
            e.messages[0]
            == "Only one of the GitHub or Job Server sections can be filled in."
        )


@pytest.mark.django_db
def test_report_all_github_and_no_job_server_fields_filled(bennett_org):
    ReportFactory(org=bennett_org, **REAL_REPO_DETAILS)


@pytest.mark.django_db
def test_report_no_github_and_all_job_server_fields_filled(bennett_org):
    report = ReportFactory(
        org=bennett_org,
        is_draft=True,
        repo="",
        branch="",
        report_html_file_path="",
        job_server_url="http://example.com/",
    )

    report.full_clean()


@pytest.mark.django_db
def test_report_no_github_and_no_job_server_fields_filled(bennett_org):
    try:
        ReportFactory(
            org=bennett_org,
            repo="",
            branch="",
            report_html_file_path="",
        ).full_clean()
    except ValidationError as e:
        assert (
            e.messages[0]
            == "Either the GitHub or Job Server sections must be filled in."
        )


@pytest.mark.django_db
def test_report_some_github_and_no_job_server_fields_filled(bennett_org):
    try:
        ReportFactory(
            org=bennett_org,
            repo="opensafely",
            branch="",
            report_html_file_path="",
        )
    except ValidationError as e:
        assert e.messages[0] == "All of the GitHub section must be completed."


@pytest.mark.django_db
def test_report_menu_name_autopopulates(bennett_org):
    report = ReportFactory(
        org=bennett_org,
        title="Fungible watermelon",
        **REAL_REPO_DETAILS,
    )
    report.full_clean()
    assert report.menu_name == "Fungible watermelon"


@pytest.mark.django_db
def test_report_menu_name_is_limited_to_sixty_characters(bennett_org):
    with pytest.raises(ValidationError, match="at most 60 characters"):
        ReportFactory(
            title="012345678901234567890123456789012345678901234567890123456789X",
            org=bennett_org,
            **REAL_REPO_DETAILS,
        )


@pytest.mark.django_db
def test_report_uses_github(bennett_org, httpretty):
    report = Report(
        org=bennett_org,
        **REAL_REPO_DETAILS,
    )
    assert report.uses_github

    httpretty.register_uri(httpretty.GET, "http://example.com", status=200)
    report = Report(
        org=bennett_org,
        job_server_url="http://example.com/",
    )
    assert not report.uses_github


@pytest.mark.django_db
def test_report_with_missing_job_server_file(bennett_org, httpretty):
    httpretty.register_uri(httpretty.HEAD, "http://example.com", status=404)

    with pytest.raises(ValidationError, match="Could not find specified file"):
        ReportFactory(
            org=bennett_org,
            repo="",
            branch="",
            report_html_file_path="",
            job_server_url="http://example.com/",
        )


@pytest.mark.django_db
def test_report_with_unpublished_output_and_published(bennett_org, httpretty):
    httpretty.register_uri(httpretty.HEAD, "http://example.com", status=200)

    msg = "Unpublished outputs cannot be used in public reports"
    with pytest.raises(ValidationError, match=msg):
        ReportFactory(
            org=bennett_org,
            is_draft=False,
            repo="",
            branch="",
            report_html_file_path="",
            job_server_url="http://example.com/",
        )


@pytest.mark.parametrize(
    "update_fields,cache_token_changed",
    [
        ({}, False),
        (
            {"description": "new"},
            True,
        ),
        ({"is_draft": False}, False),
        (
            {"report_html_file_path": "foo.html"},
            True,
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
    bennett_org,
    mock_repo_url,
    update_fields,
    cache_token_changed,
):
    mock_repo_url("https://github.com/opensafely/test")
    report = ReportFactory(
        org=bennett_org,
        title="test",
        repo="output-explorer-test-repo",
        branch="master",
        report_html_file_path="test.html",
        is_draft=False,
    )
    report_id = report.id
    initial_cache_token = report.cache_token

    # Fetch from the db again so the initial values are registered
    report = Report.objects.get(id=report_id)
    # update fields and save
    for field, value in update_fields.items():
        setattr(report, field, value)
    report.save()
    assert (initial_cache_token != report.cache_token) == cache_token_changed


@pytest.mark.django_db
def test_cache_refresh_on_report_save_with_links(bennett_org):
    report = ReportFactory(
        org=bennett_org,
        title="test",
        repo="output-explorer-test-repo",
        branch="master",
        report_html_file_path="test.html",
        is_draft=False,
    )
    initial_cache_token = report.cache_token
    # add a new link
    link = LinkFactory(report=report, url="https://test.test", label="test")
    report.refresh_from_db()
    assert initial_cache_token != report.cache_token

    # # update link
    initial_cache_token = report.cache_token
    link.icon = "github"
    link.save()
    report.refresh_from_db()
    assert initial_cache_token != report.cache_token

    # delete link
    initial_cache_token = report.cache_token
    link.delete()
    report.refresh_from_db()
    assert initial_cache_token != report.cache_token


@pytest.mark.django_db
def test_generate_repo_link_for_new_report(bennett_org, mock_repo_url):
    mock_repo_url("https://github.com/opensafely/test")
    assert Link.objects.exists() is False
    report = ReportFactory(org=bennett_org, repo="test")
    assert Link.objects.count() == 1
    link = Link.objects.first()
    assert link.url == "https://github.com/opensafely/test"

    # if the link matches the org/repo, it isn't updated on saving again.  Scheme, trailing / and case are ignored
    link.url = "http://github.com/opensafely/Test/"
    link.save()
    report.refresh_from_db()
    assert report.links.count() == 1
    assert report.links.first().url == "http://github.com/opensafely/Test/"


@pytest.mark.django_db
def test_report_save_with_multiple_links_not_including_source(
    bennett_org, mock_repo_url
):
    # Test for a bug that occurred when a report has at least one (non-source-repo) link
    # and does NOT have a source-repo link
    mock_repo_url("https://github.com/opensafely/test")
    report = ReportFactory(org=bennett_org, repo="test", branch="main")
    initial_cache_token = report.cache_token

    # This report has one link, for the source
    assert Link.objects.count() == 1
    link = Link.objects.first()
    assert link.url == "https://github.com/opensafely/test"

    # Create a second link
    Link.objects.create(report=report, url="http://test", label="test")
    report.refresh_from_db()
    cache_token_after_link_2_creation = report.cache_token
    assert cache_token_after_link_2_creation != initial_cache_token

    # Delete the source link
    assert Link.objects.count() == 2
    Link.objects.get(url="https://github.com/opensafely/test").delete()
    report.refresh_from_db()
    cache_token_after_source_link_deletion = report.cache_token
    assert cache_token_after_source_link_deletion != cache_token_after_link_2_creation

    # Save the report again; previously this resulted in a max recursion error as the
    # report attempts to create the source link again and refresh the cache token
    report.save()
    # The source link is re-created on save
    assert Link.objects.count() == 2
    assert Link.objects.filter(url="https://github.com/opensafely/test").exists()

    report.refresh_from_db()
    cache_token_after_save = report.cache_token
    assert cache_token_after_save != cache_token_after_source_link_deletion


@pytest.mark.django_db
def test_report_external():
    """
    Test the construction of an "external" Report.

    Internal and external reports are validated in Report.clean() which fires
    during model construction so we don't need to call anything explicitly here.
    """
    ReportFactory(external_description="test")


@pytest.mark.django_db
def test_report_internal(bennett_org):
    """
    Test the construction of an "internal" Report.

    Internal and external reports are validated in Report.clean() which fires
    during model construction so we don't need to call anything explicitly here.
    """
    ReportFactory(org=bennett_org, external_description="")


@pytest.mark.django_db
def test_report_incorrect_external_fields(bennett_org):
    with pytest.raises(ValidationError) as e:
        ReportFactory(external_description="")

    assert e.value.message_dict == {
        "external_description": [
            "An external description must be set for reports from external organisations."
        ]
    }

    with pytest.raises(ValidationError) as e:
        ReportFactory(org=bennett_org, external_description="test")
    assert e.value.message_dict == {
        "external_description": [
            "An external description should not be set for internal reports."
        ]
    }


@pytest.mark.django_db
def test_category_str():
    assert str(CategoryFactory(name="test")) == "test"


@pytest.mark.django_db
def test_link_str(bennett_org):
    report = ReportFactory(repo="test", external_description="test")

    assert str(report.links.first()) == "https://github.com/opensafely/test"


@pytest.mark.django_db
def test_report_refresh_cache_token_with_job_server_report(bennett_org, mocker):
    report = ReportFactory(
        org=bennett_org,
        repo="",
        branch="",
        report_html_file_path="",
        job_server_url="http://example.com",
        is_draft=True,
    )

    initial_cache_token = report.cache_token
    report.refresh_cache_token()

    assert report.cache_token != initial_cache_token


@pytest.mark.django_db
def test_report_str(bennett_org):
    assert str(ReportFactory(org=bennett_org, title="Test")) == "test"


@pytest.mark.django_db
def test_category_populated(bennett_org):
    user = UserFactory(is_staff=True)

    ReportFactory(org=bennett_org)
    category = Category.objects.get(name="Reports")
    ReportFactory(category=category, org=bennett_org)

    print(Category.objects.all())

    assert list(Category.populated.for_user(user)) == list(Category.objects.all())
