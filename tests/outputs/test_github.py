from base64 import b64encode
from datetime import date

import pytest
from github import GithubException
from model_bakery import baker

from outputs.github import GitHubOutput
from outputs.models import Output


@pytest.mark.django_db
@pytest.mark.parametrize(
    "retrieved_html",
    [
        b"""
        <html>
            <head>
                <style type="text/css">body {margin: 0;}</style>
                <style type="text/css">a {background-color: red;}</style>
                <script src="https://a-js-package.js"></script>
            </head>
            <body><p>foo</p></body>
        </html>
        """,
        b"""
        <html>
            <body><p>foo</p></body>
        </html>
        """,
        b"""
        <p>foo</p>
        """,
        b"""
        <body>
            <script>Some Javascript nonsense</script>
            <p>foo</p>
            <script>Some more Javascript nonsense</script>
        </body>
        """,
        b"""
        <body>
            <style>Mmmm, lovely styles...</style>
            <p>foo</p>
            <style>MOAR STYLZ</style>
        </body>
        """,
    ],
    ids=[
        "Extracts body from HTML full document",
        "Extracts body from HTML document without head",
        "Returns HTML without body tags unchanged",
        "Strips out all script tags",
        "Strips out all style tags",
    ],
)
def test_get_output_from_github(mock_repo, retrieved_html):
    """
    Test that html content retrieved from github is appropriately parsed
    """
    repo = mock_repo(contents=retrieved_html)
    output = baker.make(Output, output_html_file_path="foo.html")
    github_output = GitHubOutput(output, repo=repo)
    extracted_html = github_output.get_html()
    assert extracted_html == {
        "body": "<p>foo</p>",
    }


@pytest.mark.django_db
def test_get_large_html_from_github(mock_repo):
    """
    Test that a GithubException for a too-large file is caught and the content fetched
    from the git_blob by sha instead
    """
    repo = mock_repo(
        content_files=["bar.html", "foo.html"],
        blob=b64encode(b"<html><body><p>blob</p></body></html>"),
        get_contents_exception=GithubException(status=400, data={}, headers={}),
    )
    output = baker.make(Output, output_html_file_path="foo.html")
    assert output.use_git_blob is False
    assert repo.get_contents.call_count == 0

    github_output = GitHubOutput(output, repo=repo)
    extracted_html = github_output.get_html()
    output.refresh_from_db()
    assert extracted_html == {"body": "<p>blob</p>"}
    assert output.last_updated == date(2021, 4, 27)

    # After the first get_html call, use_git_blob is set to avoid re-attempting to call
    # get_contents on the single file, which will fail
    # get_contents is called twice, once on the single file, once for the parent folder contents
    assert repo.get_contents.call_count == 2
    assert output.use_git_blob is True

    # re-fetch; get_contents is not called again on the single file, only on the parent folder
    extracted_html = github_output.get_html()
    assert extracted_html == {"body": "<p>blob</p>"}
    assert repo.get_contents.call_count == 3


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
