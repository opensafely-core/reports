import pytest
from django.utils import timezone
from django.utils.http import http_date
from model_bakery import baker

from reports.job_server import JobServerClient, JobServerReport
from reports.models import Report


@pytest.mark.django_db
def test_get_html_caches(httpretty):
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

    report = baker.make(Report, job_server_url=url)
    assert len(httpretty.latest_requests()) == 1

    job_server_report = JobServerReport(report)

    job_server_report.get_html()
    assert len(httpretty.latest_requests()) == 3

    job_server_report.get_html()
    assert len(httpretty.latest_requests()) == 3


@pytest.mark.django_db
def test_get_published_html_from_job_server(httpretty):
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
        responses=[httpretty.Response(status=200, body=expected_html)],
    )

    report = baker.make(Report, job_server_url=url)
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
