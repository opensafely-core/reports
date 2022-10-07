from datetime import timedelta

import pytest
from django.utils import timezone
from django.utils.http import http_date

from reports.job_server import JobServerClient, JobServerReport

from ..factories import ReportFactory


@pytest.mark.django_db
def test_clear_cache_with_non_caching_session(httpretty, bennett_org):
    url = "https://jobs.opensafely.org/org/project/workspace/published/file_id"

    # Mock the job-server file_exists() request
    httpretty.register_uri(
        httpretty.HEAD, url, responses=[httpretty.Response(status=200, body="")]
    )

    report = ReportFactory(
        org=bennett_org,
        job_server_url=url,
        repo="",
        branch="",
        report_html_file_path="",
    )

    # check a non-caching version works
    JobServerReport(report, use_cache=False).clear_cache()


@pytest.mark.django_db
def test_clear_cache_with_caching_session(httpretty, bennett_org):
    expected_html = """
    <html>
        <body><p>foo</p></body>
    </html>
    """
    url = "https://jobs.opensafely.org/org/project/workspace/published/file_id"

    # Mock the job-server file_exists() request
    httpretty.register_uri(
        httpretty.HEAD, url, responses=[httpretty.Response(status=200, body="")]
    )

    httpretty.register_uri(
        httpretty.GET,
        url,
        responses=[
            httpretty.Response(
                status=200,
                body=expected_html,
                adding_headers={"Last-Modified": http_date(timezone.now().timestamp())},
            )
        ],
    )

    report = ReportFactory(
        org=bennett_org,
        job_server_url=url,
        repo="",
        branch="",
        report_html_file_path="",
    )

    wrapper = JobServerReport(report, use_cache=True)

    wrapper.get_html()
    assert url in list(wrapper.client.session.cache.urls)

    wrapper.clear_cache()
    assert url not in list(wrapper.client.session.cache.urls)


@pytest.mark.django_db
def test_get_html_caches(httpretty, bennett_org):
    expected_html = """
    <html>
        <body><p>foo</p></body>
    </html>
    """
    url = "https://jobs.opensafely.org/org/project/workspace/published/file_id"

    # Mock the job-server file_exists() request
    httpretty.register_uri(
        httpretty.HEAD, url, responses=[httpretty.Response(status=200, body="")]
    )

    httpretty.register_uri(
        httpretty.GET,
        url,
        responses=[
            httpretty.Response(
                status=200,
                body=expected_html,
                adding_headers={"Last-Modified": http_date(timezone.now().timestamp())},
            )
        ],
    )

    report = ReportFactory(
        org=bennett_org,
        job_server_url=url,
        repo="",
        branch="",
        report_html_file_path="",
    )
    assert len(httpretty.latest_requests()) == 1

    job_server_report = JobServerReport(report)

    job_server_report.get_html()
    assert len(httpretty.latest_requests()) == 3

    job_server_report.get_html()
    assert len(httpretty.latest_requests()) == 3


@pytest.mark.django_db
def test_get_published_html_from_job_server(httpretty, bennett_org):
    expected_html = """
    <html>
        <body><p>foo</p></body>
    </html>
    """
    url = "https://jobs.opensafely.org/org/project/workspace/published/file_id"

    # Mock the job-server file_exists() request
    httpretty.register_uri(
        httpretty.HEAD, url, responses=[httpretty.Response(status=200, body="")]
    )

    # Mock the job-server get_file() request
    httpretty.register_uri(
        httpretty.GET,
        url,
        responses=[
            httpretty.Response(
                status=200,
                body=expected_html,
                adding_headers={"Last-Modified": http_date(timezone.now().timestamp())},
            )
        ],
    )

    report = ReportFactory(
        org=bennett_org,
        job_server_url=url,
        repo="",
        branch="",
        report_html_file_path="",
    )
    job_server_report = JobServerReport(report)
    assert job_server_report.get_html() == expected_html


@pytest.mark.django_db
def test_get_unpublished_html_from_job_server(httpretty):
    url = "https://jobs.opensafely.org/api/v2/releases/file/file_id"

    # Mock the job-server file_exists() request
    httpretty.register_uri(
        httpretty.HEAD,
        url,
        responses=[
            httpretty.Response(status=200, body=""),
        ],
    )

    JobServerClient(token="test").file_exists(url)

    assert httpretty.latest_requests()[0].headers["Authorization"] == "test"


@pytest.mark.django_db
def test_last_updated(httpretty, bennett_org):
    expected_html = """
    <html>
        <body><p>foo</p></body>
    </html>
    """
    url = "https://jobs.opensafely.org/org/project/workspace/published/file_id"

    # Mock the job-server file_exists() request
    httpretty.register_uri(
        httpretty.HEAD, url, responses=[httpretty.Response(status=200, body="")]
    )

    httpretty.register_uri(
        httpretty.GET,
        url,
        responses=[
            httpretty.Response(
                status=200,
                body=expected_html,
                adding_headers={"Last-Modified": http_date(timezone.now().timestamp())},
            )
        ],
    )

    report = ReportFactory(
        org=bennett_org,
        job_server_url=url,
        repo="",
        branch="",
        report_html_file_path="",
    )
    job_server_report = JobServerReport(report)

    assert job_server_report.last_updated() == report.last_updated


@pytest.mark.django_db
def test_report_last_updated_after_fetching(httpretty, bennett_org):
    expected_html = """
    <html>
        <body><p>foo</p></body>
    </html>
    """
    url = "https://jobs.opensafely.org/org/project/workspace/published/file_id"

    # Mock the job-server file_exists() request
    httpretty.register_uri(
        httpretty.HEAD, url, responses=[httpretty.Response(status=200, body="")]
    )

    now = timezone.now()

    # Mock the job-server get_file() request
    httpretty.register_uri(
        httpretty.GET,
        url,
        responses=[
            httpretty.Response(
                status=200,
                body=expected_html,
                adding_headers={"Last-Modified": http_date(now.timestamp())},
            )
        ],
    )

    report = ReportFactory(
        org=bennett_org,
        job_server_url=url,
        last_updated=now - timedelta(days=5),
        repo="",
        branch="",
        report_html_file_path="",
    )

    JobServerReport(report).get_html()
    report.refresh_from_db()
    assert report.last_updated == now.date()

    # check we don't write to the report when last_updated is the same
    JobServerReport(report).get_html()
    report.refresh_from_db()
    assert report.last_updated == now.date()
