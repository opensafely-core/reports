import datetime
from os import environ

import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
from model_bakery import baker

from reports.models import Category, Link, Report


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
    fields, expected_valid, expected_errors, reset_environment_after_test
):
    """Fetch and extract html from a real repo"""
    environ["GITHUB_VALIDATION"] = "True"
    report_fields = {**REAL_REPO_DETAILS, **fields}
    if not expected_valid:
        with pytest.raises(ValidationError, match=expected_errors):
            baker.make(Report, **report_fields)
    else:
        baker.make(Report, **report_fields)


@pytest.mark.django_db
def test_category_manager(mock_repo_url):
    # one category exists already, from the migrations.
    category = Category.objects.first()
    # Create a second category; neither have any associated Reports
    baker.make(Category, name="test")

    # No populated categories
    assert Category.populated.exists() is False
    mock_repo_url("https://github.com/opensafely/test-repo")
    baker.make_recipe("reports.dummy_report", category=category)
    # 2 category objects, only one populated
    assert Category.objects.count() == 2
    assert Category.populated.count() == 1
    assert Category.populated.first() == category


@pytest.mark.django_db
def test_category_for_user(user_no_permission, user_with_permission, mock_repo_url):
    category = Category.objects.first()
    draft_category = baker.make(Category, name="test")
    mock_repo_url("https://github.com/opensafely/test-repo")
    baker.make_recipe("reports.dummy_report", category=category)
    baker.make_recipe("reports.dummy_report", category=draft_category, is_draft=True)

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
def test_archive_category_for_user(
    user_no_permission, user_with_permission, mock_repo_url
):
    # Archive category is never returned in the populated_for_user manager
    category = Category.objects.first()
    archive_category = baker.make(Category, name="Archive")
    mock_repo_url("https://github.com/opensafely/test-repo")
    baker.make_recipe("reports.dummy_report", category=category)
    baker.make_recipe("reports.dummy_report", category=archive_category)

    user = AnonymousUser()
    assert list(Category.populated.for_user(user)) == list(
        Category.objects.filter(id=category.id)
    )
    assert list(Category.populated.for_user(user_no_permission)) == list(
        Category.objects.filter(id=category.id)
    )
    assert list(Category.populated.for_user(user_with_permission)) == list(
        Category.objects.filter(id=category.id)
    )


@pytest.mark.django_db
def test_report_all_github_and_all_job_server_fields_filled():
    category = baker.make(Category, name="test")
    report = Report(
        title="Fungible watermelon",
        category=category,
        publication_date=datetime.date.today(),
        description="A description",
        job_server_url="http://example.com/",
        **REAL_REPO_DETAILS,
    )

    try:
        report.full_clean()
    except ValidationError as e:
        assert (
            e.messages[0]
            == "Only one of the GitHub or Job Server sections can be filled in."
        )


@pytest.mark.django_db
def test_report_all_github_and_no_job_server_fields_filled():
    category = baker.make(Category, name="test")
    report = Report(
        title="Fungible watermelon",
        category=category,
        publication_date=datetime.date.today(),
        description="A description",
        **REAL_REPO_DETAILS,
    )

    report.full_clean()


@pytest.mark.django_db
def test_report_no_github_and_all_job_server_fields_filled():
    category = baker.make(Category, name="test")
    report = Report(
        title="Fungible watermelon",
        category=category,
        publication_date=datetime.date.today(),
        description="A description",
        is_draft=True,
        job_server_url="http://example.com/",
    )

    report.full_clean()


@pytest.mark.django_db
def test_report_no_github_and_no_job_server_fields_filled():
    category = baker.make(Category, name="test")
    report = Report(
        title="Fungible watermelon",
        category=category,
        publication_date=datetime.date.today(),
        description="A description",
    )

    try:
        report.full_clean()
    except ValidationError as e:
        assert (
            e.messages[0]
            == "Either the GitHub or Job Server sections must be filled in."
        )


@pytest.mark.django_db
def test_report_some_github_and_no_job_server_fields_filled():
    category = baker.make(Category, name="test")
    report = Report(
        title="Fungible watermelon",
        category=category,
        publication_date=datetime.date.today(),
        description="A description",
        repo="opensafely",
    )

    try:
        report.full_clean()
    except ValidationError as e:
        assert e.messages[0] == "All of the GitHub section must be completed."


@pytest.mark.django_db
def test_report_menu_name_autopopulates():
    category = baker.make(Category, name="test")
    report = Report(
        title="Fungible watermelon",
        category=category,
        publication_date=datetime.date.today(),
        description="A description",
        **REAL_REPO_DETAILS,
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
        **REAL_REPO_DETAILS,
    )
    with pytest.raises(ValidationError, match="at most 60 characters"):
        report.full_clean()


@pytest.mark.django_db
def test_report_uses_github(httpretty):
    category = baker.make(Category, name="test")

    report = Report(
        title="Fungible watermelon",
        category=category,
        publication_date=datetime.date.today(),
        description="A description",
        **REAL_REPO_DETAILS,
    )
    assert report.uses_github

    httpretty.register_uri(httpretty.GET, "http://example.com", status=200)
    report = Report(
        title="Fungible watermelon",
        category=category,
        publication_date=datetime.date.today(),
        description="A description",
        job_server_url="http://example.com/",
    )
    assert not report.uses_github


@pytest.mark.django_db
def test_report_with_missing_job_server_file(httpretty):
    httpretty.register_uri(httpretty.HEAD, "http://example.com", status=404)

    category = baker.make(Category, name="test")
    report = Report(
        title="Fungible watermelon",
        category=category,
        publication_date=datetime.date.today(),
        description="A description",
        job_server_url="http://example.com/",
    )

    with pytest.raises(ValidationError, match="Could not find specified file"):
        report.full_clean()


@pytest.mark.django_db
def test_report_with_unpublished_output_and_published(httpretty):
    httpretty.register_uri(httpretty.HEAD, "http://example.com", status=200)

    category = baker.make(Category, name="test")
    report = Report(
        title="Fungible watermelon",
        category=category,
        publication_date=datetime.date.today(),
        description="A description",
        is_draft=False,
        job_server_url="http://example.com/",
    )

    msg = "Unpublished outputs cannot be used in public reports"
    with pytest.raises(ValidationError, match=msg):
        report.full_clean()


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
    mock_repo_url,
    update_fields,
    cache_token_changed,
):
    mock_repo_url("https://github.com/opensafely/test")
    report = baker.make(
        Report,
        category=Category.objects.first(),
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
def test_cache_refresh_on_report_save_with_links(mock_repo_url):
    mock_repo_url("https://github.com/opensafely/test")
    report = baker.make(
        Report,
        category=Category.objects.first(),
        title="test",
        repo="output-explorer-test-repo",
        branch="master",
        report_html_file_path="test.html",
        is_draft=False,
    )
    initial_cache_token = report.cache_token
    # add a new link
    link = baker.make(Link, report=report, url="https://test.test", label="test")
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
def test_generate_repo_link_for_new_report(mock_repo_url):
    mock_repo_url("https://github.com/opensafely/test")
    assert Link.objects.exists() is False
    report = baker.make_recipe("reports.dummy_report", repo="test")
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
def test_report_save_with_multiple_links_not_including_source(mock_repo_url):
    # Test for a bug that occurred when a report has at least one (non-source-repo) link
    # and does NOT have a source-repo link
    mock_repo_url("https://github.com/opensafely/test")
    report = baker.make_recipe("reports.dummy_report", repo="test", branch="main")
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
