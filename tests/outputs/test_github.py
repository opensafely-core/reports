import json
from base64 import b64encode
from datetime import date
from os import environ

import pytest
from model_bakery import baker
from requests.exceptions import HTTPError

from outputs.github import GithubAPIException, GithubClient, GitHubOutput, GithubRepo
from outputs.models import Output


def register_commits_uri(httpretty, owner, repo, path, sha, commit_dates):
    commit_dates = (
        [commit_dates] if not isinstance(commit_dates, list) else commit_dates
    )
    httpretty.register_uri(
        httpretty.GET,
        f"https://api.github.com/repos/{owner}/{repo}/commits?sha={sha}&path={path}",
        status=200,
        body=json.dumps(
            [
                {"commit": {"committer": {"date": commit_date}}}
                for commit_date in commit_dates
            ]
        ),
    )


def test_github_client_get_repo(httpretty):
    # Mock the github request
    httpretty.register_uri(
        httpretty.GET,
        "https://api.github.com/repos/test/foo",
        status=200,
        body=json.dumps({"name": "foo"}),
    )
    client = GithubClient()
    repo = client.get_repo("test/foo")
    assert repo.repo_path_segments == ["repos", "test", "foo"]


def test_github_client_token(reset_environment_after_test):
    """Authorization headers is set based on environment variable"""
    environ["GITHUB_TOKEN"] = "test"
    client = GithubClient()
    assert client.headers["Authorization"] == "token test"

    del environ["GITHUB_TOKEN"]
    client = GithubClient()
    assert "Authorization" not in client.headers


def test_github_client_get_repo_not_found(httpretty):
    # Mock the github request
    httpretty.register_uri(
        httpretty.GET,
        "https://api.github.com/repos/test/bar",
        status=404,
        body=json.dumps({"message": "Not found"}),
    )
    client = GithubClient()
    with pytest.raises(GithubAPIException, match="Not found"):
        client.get_repo("test/bar")


@pytest.mark.parametrize("use_cache", [True, False])
def test_github_client_get_repo_with_cache(httpretty, use_cache):
    client = GithubClient(use_cache=use_cache)

    # set up mock request with valid response and call it
    httpretty.register_uri(
        httpretty.GET,
        "https://api.github.com/repos/test/test-cache",
        status=200,
        body=json.dumps({"name": "foo"}),
    )
    client.get_repo("test/test-cache")

    # re-mock the repos request to a 404, should raise an exception if called directly
    httpretty.register_uri(
        httpretty.GET,
        "https://api.github.com/repos/test/test-cache",
        status=404,
        body=json.dumps({"message": "Not found"}),
    )
    if use_cache:
        # No exception raised because the first response was cached
        client.get_repo("test/test-cache")
    else:
        # Exception raised because the repos endpoint was fetched again
        with pytest.raises(GithubAPIException, match="Not found"):
            client.get_repo("test/test-cache")


def test_github_repo_get_contents_single_file(httpretty):
    repo = GithubRepo(client=GithubClient(use_cache=False), owner="test", name="foo")
    str_content = """
        <html>
            <head>
                <style type="text/css">body {margin: 0;}</style>
                <style type="text/css">a {background-color: red;}</style>
                <script src="https://a-js-package.js"></script>
            </head>
            <body><p>foo</p></body>
        </html>
    """
    # Content retrieved from GitHub is base64-encoded, decoded to str for json
    b64_content = b64encode(bytes(str_content, encoding="utf-8")).decode()
    # Mock the github request
    httpretty.register_uri(
        httpretty.GET,
        "https://api.github.com/repos/test/foo/contents/test-folder%2Ftest-file.html?ref=master",
        status=200,
        body=json.dumps(
            {
                "name": "test-file.html",
                "path": "test-folder/test-file.html",
                "sha": "abcd1234",
                "size": 1234,
                "encoding": "base64",
                "content": b64_content,
            }
        ),
    )
    # commits uri is also called, to get the last_updated date
    register_commits_uri(
        httpretty,
        owner="test",
        repo="foo",
        path="test-folder%2Ftest-file.html",
        sha="master",
        commit_dates="2021-03-01T10:00:00Z",
    )

    content_file = repo.get_contents("test-folder/test-file.html", ref="master")
    assert content_file.name == "test-file.html"
    # decoded content retrieves the original str contents
    assert content_file.decoded_content == str_content


def test_github_repo_get_last_updated(httpretty):
    repo = GithubRepo(client=GithubClient(use_cache=False), owner="test", name="foo")
    register_commits_uri(
        httpretty,
        owner="test",
        repo="foo",
        path="test-folder%2Ftest-file.html",
        sha="master",
        commit_dates=[
            "2021-03-01T10:00:00Z",
            "2021-02-14T10:00:00Z",
            "2021-02-01T10:00:00Z",
        ],
    )

    last_updated = repo.get_last_updated(
        path="test-folder/test-file.html", ref="master"
    )
    assert last_updated == date(2021, 3, 1)


@pytest.mark.parametrize(
    "status_code,body,expected_exception,expected_match",
    [
        (
            403,
            {"errors": [{"code": "too_large", "message": "File was too large"}]},
            GithubAPIException,
            "Error: File too large",
        ),
        (404, {"message": "Not found"}, GithubAPIException, "Not found"),
        (
            403,
            {"errors": [{"code": "other_code", "message": "An unexpected 403"}]},
            HTTPError,
            "Forbidden for url",
        ),
        (
            401,
            {"errors": [{"code": "other_code", "message": "An unexpected 403"}]},
            HTTPError,
            "Unauthorized for url",
        ),
    ],
)
def test_github_repo_get_contents_exceptions(
    httpretty, status_code, body, expected_exception, expected_match
):
    """
    Test expected and unexpected exceptions from get_contents
    """
    repo = GithubRepo(client=GithubClient(use_cache=False), owner="test", name="foo")
    # Mock the github request
    httpretty.register_uri(
        httpretty.GET,
        "https://api.github.com/repos/test/foo/contents/test-folder%2Ftest-file.html?ref=master",
        status=status_code,
        body=json.dumps(body),
    )
    with pytest.raises(expected_exception, match=expected_match):
        repo.get_contents("test-folder/test-file.html", ref="master")


def test_github_repo_get_contents_folder(httpretty):
    repo = GithubRepo(client=GithubClient(use_cache=False), owner="test", name="foo")
    # Mock the github request
    httpretty.register_uri(
        httpretty.GET,
        "https://api.github.com/repos/test/foo/contents/test-folder?ref=master",
        status=200,
        body=json.dumps(
            [
                {
                    "name": "test-file1.html",
                    "path": "test-folder/test-file1.html",
                    "sha": "abcd1234",
                    "size": 1234,
                    "encoding": "base64",
                },
                {
                    "name": "test-file2.html",
                    "path": "test-folder/test-file2.html",
                    "sha": "abcd5678",
                    "size": 1234,
                    "encoding": "base64",
                },
            ]
        ),
    )
    contents = repo.get_contents("test-folder", ref="master")
    assert isinstance(contents, list)
    assert len(contents) == 2
    assert contents[0].name == "test-file1.html"
    assert contents[1].name == "test-file2.html"


def test_github_repo_get_git_blob(httpretty):
    repo = GithubRepo(client=GithubClient(use_cache=False), owner="test", name="foo")
    str_content = """
        <html>
            <head>
                <style type="text/css">body {margin: 0;}</style>
                <style type="text/css">a {background-color: red;}</style>
                <script src="https://a-js-package.js"></script>
            </head>
            <body><p>foo</p></body>
        </html>
    """
    # Content retrieved from GitHub is base64-encoded, decoded to str for json
    b64_content = b64encode(bytes(str_content, encoding="utf-8")).decode()
    # Mock the github request
    httpretty.register_uri(
        httpretty.GET,
        "https://api.github.com/repos/test/foo/git/blobs/abcd1234",
        status=200,
        body=json.dumps(
            {
                "name": "test-file.html",
                "path": "test-folder/test-file.html",
                "sha": "abcd1234",
                "size": 1234,
                "encoding": "base64",
                "content": b64_content,
            }
        ),
    )
    register_commits_uri(
        httpretty,
        owner="test",
        repo="foo",
        path="test-folder%2Ftest-file.html",
        sha="master",
        commit_dates="2021-03-01T10:00:00Z",
    )
    content_file = repo.get_git_blob("abcd1234", None)
    assert content_file.name == "test-file.html"
    # decoded content retrieves the original str contents
    assert content_file.decoded_content == str_content


@pytest.mark.django_db
@pytest.mark.parametrize(
    "retrieved_html",
    [
        b64encode(
            b"""
        <html>
            <head>
                <style type="text/css">body {margin: 0;}</style>
                <style type="text/css">a {background-color: red;}</style>
                <script src="https://a-js-package.js"></script>
            </head>
            <body><p>foo</p></body>
        </html>
        """
        ).decode(),
        b64encode(
            b"""
        <html>
            <body><p>foo</p></body>
        </html>
        """
        ).decode(),
        b64encode(
            b"""
        <p>foo</p>
        """
        ).decode(),
        b64encode(
            b"""
        <body>
            <script>Some Javascript nonsense</script>
            <p>foo</p>
            <script>Some more Javascript nonsense</script>
        </body>
        """
        ).decode(),
        b64encode(
            b"""
        <body>
            <style>Mmmm, lovely styles...</style>
            <p>foo</p>
            <style>MOAR STYLZ</style>
        </body>
        """
        ).decode(),
    ],
    ids=[
        "Extracts body from HTML full document",
        "Extracts body from HTML document without head",
        "Returns HTML without body tags unchanged",
        "Strips out all script tags",
        "Strips out all style tags",
    ],
)
def test_get_output_from_github(httpretty, retrieved_html):
    """
    Test that html content retrieved from github is appropriately parsed
    """
    repo = GithubRepo(GithubClient(use_cache=False), name="test", owner="test")
    output = baker.make(Output, output_html_file_path="foo.html")
    # Mock the github request
    httpretty.register_uri(
        httpretty.GET,
        "https://api.github.com/repos/test/test/contents/foo.html?ref=main",
        responses=[
            httpretty.Response(
                status=200,
                body=json.dumps(
                    {"name": "foo.html", "sha": "abcd1234", "content": retrieved_html}
                ),
                adding_headers={"Last-Modified": "Tue, 27 Apr 2021 10:00:00 GMT"},
            )
        ],
    )
    register_commits_uri(
        httpretty,
        owner="test",
        repo="test",
        path="foo.html",
        sha="main",
        commit_dates="2021-04-25T10:00:00Z",
    )

    github_output = GitHubOutput(output, repo=repo)
    extracted_html = github_output.get_html()
    assert extracted_html == {
        "body": "<p>foo</p>",
    }


@pytest.mark.django_db
def test_get_large_html_from_github(httpretty):
    """
    Test that a GithubException for a too-large file is caught and the content fetched
    from the git_blob by sha instead
    """
    # Mock the github requests
    # /contents on the too-large file returns a 403
    httpretty.register_uri(
        httpretty.GET,
        "https://api.github.com/repos/test/test/contents/foo.html?ref=main",
        status=403,
        body=json.dumps({"errors": [{"code": "too_large"}]}),
    )
    # /contents on the parent folder returns two files
    httpretty.register_uri(
        httpretty.GET,
        "https://api.github.com/repos/test/test/contents/?ref=main",
        status=200,
        body=json.dumps(
            [
                {"name": "bar.html", "sha": "abcd9999"},
                {"name": "foo.html", "sha": "abcd1234"},
            ]
        ),
        adding_headers={"Last-Modified": "Tue, 27 Apr 2021 10:00:00 GMT"},
    )
    # /git/blobs on the sha from the found file in the parent folder
    httpretty.register_uri(
        httpretty.GET,
        "https://api.github.com/repos/test/test/git/blobs/abcd1234",
        status=200,
        body=json.dumps(
            {
                "name": "foo.html",
                "path": "foo.html",
                "sha": "abcd1234",
                "size": 1234,
                "encoding": "base64",
                "content": b64encode(b"<html><body><p>blob</p></body></html>").decode(),
            }
        ),
    )
    register_commits_uri(
        httpretty,
        owner="test",
        repo="test",
        path="foo.html",
        sha="main",
        commit_dates="2021-04-25T10:00:00Z",
    )

    repo = GithubRepo(client=GithubClient(use_cache=False), owner="test", name="test")
    output = baker.make(Output, output_html_file_path="foo.html")
    assert output.use_git_blob is False

    github_output = GitHubOutput(output, repo=repo)
    extracted_html = github_output.get_html()
    output.refresh_from_db()
    assert extracted_html == {"body": "<p>blob</p>"}
    # last updated date is retrieved from the last commmit
    assert output.last_updated == date(2021, 4, 25)

    # 4 calls were made, to /contents and /commits for the single file and its updated date,
    # then to /contents for the parent folder, and /git/blob for the file contents
    assert len(httpretty.latest_requests()) == 4

    # After the first get_html call, use_git_blob is set to avoid re-attempting to call
    # get_contents on the single file, which will fail
    # get_contents is called twice, once on the single file, once for the parent folder contents
    assert output.use_git_blob is True

    # # re-fetch; get_contents is not called again on the single file, only on the parent folder
    extracted_html = github_output.get_html()
    assert extracted_html == {"body": "<p>blob</p>"}
    # Only 3 more calls, to /contents for the parent folder, /commits for the update date
    # and /git/blob for the file contents
    latest_requests = httpretty.latest_requests()
    assert len(latest_requests) == 7
    assert (
        latest_requests[-3].url
        == "https://api.github.com/repos/test/test/contents/?ref=main"
    )
    assert (
        latest_requests[-2].url
        == "https://api.github.com/repos/test/test/commits?sha=main&path=foo.html"
    )
    assert (
        latest_requests[-1].url
        == "https://api.github.com/repos/test/test/git/blobs/abcd1234"
    )


@pytest.mark.django_db
def test_github_output_get_parent_contents_invalid_folder(httpretty):
    repo = GithubRepo(
        client=GithubClient(use_cache=False), owner="test", name="test-folder"
    )
    output = baker.make(Output, output_html_file_path="test-folder/foo.html")

    # Mock the github request
    httpretty.register_uri(
        httpretty.GET,
        "https://api.github.com/repos/test/test-folder/contents/test-folder?ref=main",
        status=404,
        body=json.dumps({"message": "Not found"}),
    )
    github_output = GitHubOutput(output, repo=repo)
    with pytest.raises(GithubAPIException, match="Not found"):
        github_output.get_parent_contents()


@pytest.mark.django_db
def test_integration():
    """Fetch and extract html from a real repo"""
    output = baker.make(
        Output,
        repo="output-explorer-test-repo",
        branch="master",
        output_html_file_path="test-outputs/output.html",
    )
    output.clean()
    github_output = GitHubOutput(output)
    extracted_html = github_output.get_html()
    assert extracted_html == {
        "body": "<h1>A Test Output HTML file</h1>\n<p>The test content\t\n</p>",
    }
