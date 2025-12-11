import json
from base64 import b64encode
from datetime import date

import pytest
import responses
from osgithub import GithubAPIException, GithubClient, GithubRepo

from reports.github import GithubReport

from ..factories import ReportFactory


def register_commits_uri(http_responses, owner, repo, path, sha, commit_dates):
    commit_dates = (
        [commit_dates] if not isinstance(commit_dates, list) else commit_dates
    )
    http_responses.add(
        responses.GET,
        f"https://api.github.com/repos/{owner}/{repo}/commits?sha={sha}&path={path}&per_page=1",
        status=200,
        body=json.dumps(
            [
                {"commit": {"committer": {"date": commit_date}}}
                for commit_date in commit_dates
            ]
        ),
    )


@pytest.mark.django_db
def test_get_normal_html_from_github(http_responses, bennett_org):
    html = """
        <html>
            <body><p>foo</p></body>
        </html>
    """
    # Mock the github request
    http_responses.add(
        responses.GET,
        "https://api.github.com/repos/opensafely/test/contents/foo.html?ref=main",
        status=200,
        body=json.dumps(
            {
                "name": "foo.html",
                "sha": "abcd1234",
                "content": b64encode(html.encode()).decode(),
            }
        ),
        headers={"Last-Modified": "Tue, 27 Apr 2021 10:00:00 GMT"},
    )
    register_commits_uri(
        http_responses,
        owner="opensafely",
        repo="test",
        path="foo.html",
        sha="main",
        commit_dates="2021-04-25T10:00:00Z",
    )
    repo = GithubRepo(GithubClient(use_cache=False), name="test", owner="opensafely")
    report = ReportFactory(
        org=bennett_org, repo="test", branch="main", report_html_file_path="foo.html"
    )
    github_report = GithubReport(report, repo=repo)
    assert github_report.get_html() == html


@pytest.mark.django_db
def test_get_large_html_from_github(bennett_org, http_responses):
    """
    Test that a GithubException for a too-large file is caught and the content fetched
    from the git_blob by sha instead
    """
    html = """
        <html>
            <body><p>foo</p></body>
        </html>
    """
    # Mock the github requests
    # /contents on the too-large file returns a 403
    http_responses.add(
        responses.GET,
        "https://api.github.com/repos/opensafely/test/contents/foo.html?ref=main",
        status=200,
        body=json.dumps(
            {
                "name": "foo.html",
                "path": "foo.html",
                "sha": "abcd1234",
                "size": 1234,
                "encoding": "base64",
                "content": "",
            }
        ),
    )
    # /contents on the parent folder returns two files
    http_responses.add(
        responses.GET,
        "https://api.github.com/repos/opensafely/test/contents/?ref=main",
        status=200,
        body=json.dumps(
            [
                {"name": "bar.html", "sha": "abcd9999"},
                {"name": "foo.html", "sha": "abcd1234"},
            ]
        ),
        headers={"Last-Modified": "Tue, 27 Apr 2021 10:00:00 GMT"},
    )
    # /git/blobs on the sha from the found file in the parent folder
    http_responses.add(
        responses.GET,
        "https://api.github.com/repos/opensafely/test/git/blobs/abcd1234",
        status=200,
        body=json.dumps(
            {
                "name": "foo.html",
                "path": "foo.html",
                "sha": "abcd1234",
                "size": 1234,
                "encoding": "base64",
                "content": b64encode(html.encode()).decode(),
            }
        ),
    )
    register_commits_uri(
        http_responses,
        owner="opensafely",
        repo="test",
        path="foo.html",
        sha="main",
        commit_dates="2021-04-25T10:00:00Z",
    )

    repo = GithubRepo(
        client=GithubClient(use_cache=False), owner="opensafely", name="test"
    )
    report = ReportFactory(
        org=bennett_org, repo="test", branch="main", report_html_file_path="foo.html"
    )
    assert report.use_git_blob is False

    github_report = GithubReport(report, repo=repo)
    report.refresh_from_db()
    assert github_report.get_html() == html
    # last updated date is retrieved from the last commmit
    assert report.last_updated == date(2021, 4, 25)

    # 4 calls were made, to /contents and /commits for the single file and its updated date,
    # then to /contents for the parent folder, and /git/blob for the file contents
    assert len(http_responses.calls) == 4

    # After the first get_html call, use_git_blob is set to avoid re-attempting to call
    # get_contents on the single file, which will fail
    # get_contents is called twice, once on the single file, once for the parent folder contents
    assert report.use_git_blob is True

    # refetch; the html has now been stored on the GithubReport, so no additional calls are made
    assert github_report.get_html() == html
    latest_requests = http_responses.calls
    assert len(latest_requests) == 4

    # instantiate a new GithubReport and re-fetch; get_contents is not called again on the single file,
    # only on the parent folder
    github_report = GithubReport(report, repo=repo)
    assert github_report.get_html() == html
    # Only 3 more calls, to /contents for the parent folder, /git/blob for the file contents
    # and /commits for the update date
    latest_requests = http_responses.calls
    assert len(latest_requests) == 7
    assert (
        latest_requests[-3].request.url
        == "https://api.github.com/repos/opensafely/test/contents/?ref=main"
    )
    assert (
        latest_requests[-2].request.url
        == "https://api.github.com/repos/opensafely/test/git/blobs/abcd1234"
    )
    assert (
        latest_requests[-1].request.url
        == "https://api.github.com/repos/opensafely/test/commits?sha=main&path=foo.html&per_page=1"
    )


@pytest.mark.django_db
def test_github_report_get_parent_contents_invalid_folder(bennett_org, http_responses):
    http_responses.add(
        responses.GET,
        "https://api.github.com/repos/opensafely/test-repo/contents/test-folder?ref=main",
        status=404,
        body=json.dumps({"message": "Not found"}),
    )
    repo = GithubRepo(
        client=GithubClient(use_cache=False), owner="opensafely", name="test-repo"
    )
    report = ReportFactory(
        org=bennett_org,
        repo="test-repo",
        branch="main",
        report_html_file_path="test-folder/foo.html",
    )

    github_report = GithubReport(report, repo=repo)
    with pytest.raises(GithubAPIException, match="Not found"):
        github_report.get_parent_contents()


@pytest.mark.django_db
def test_integration(bennett_org):
    """Fetch and extract html from a real repo"""
    report = ReportFactory(
        org=bennett_org,
        repo="output-explorer-test-repo",
        branch="master",
        report_html_file_path="test-outputs/output.html",
    )
    report.clean()
    github_report = GithubReport(report)
    extracted_html = github_report.get_html()
    assert (
        extracted_html
        == """<!DOCTYPE html>
<html>
<head><meta charset="utf-8" />

<title>Test output</title>

<script src="https://cdnjs.cloudflare.com/ajax/libs/require.js/2.1.10/require.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/2.0.3/jquery.min.js"></script>

<style type="text/css">body {margin: 0;}</style>
<style type="text/css">a {background-color: blue;}</style>

</head>

<body>
    <h1>A Test Output HTML file</h1>
    <p>The test content</p>
</body>

</html>
"""
    )
