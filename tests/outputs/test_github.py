from base64 import b64encode
from datetime import date

import pytest
from github import GithubException
from model_bakery import baker

from outputs.github import GitHubOutput
from outputs.models import Output


@pytest.mark.django_db
def test_get_html_from_github(mock_repo):
    """
    Test that html content retrieved from github is appropriately parsed
    """
    repo = mock_repo(
        contents=b"""
        <html>
            <head>
                <style type="text/css">body {margin: 0;}</style>
                <style type="text/css">a {background-color: red;}</style>
                <script src="https://a-js-package.js"></script>
            </head>
            <body><p>foo</p></body>
        </html>
        """
    )
    output = baker.make(Output, output_html_file_path="foo.html")
    github_output = GitHubOutput(output, repo=repo)
    extracted_html = github_output.get_html()
    assert extracted_html == {
        "body": "<p>foo</p>",
        "style": [
            '<style type="text/css">body {margin: 0;}</style>',
            '<style type="text/css">a {background-color: red;}</style>',
        ],
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
    github_output = GitHubOutput(output, repo=repo)
    extracted_html = github_output.get_html()
    assert extracted_html == {"body": "<p>blob</p>", "style": []}
    assert output.last_updated == date(2021, 4, 27)


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
        "body": "\n<h1>A Test Output HTML file</h1>\n<p>The test content\t\n</p>",
        "style": [
            '<style type="text/css">body {margin: 0;}</style>',
            '<style type="text/css">a {background-color: blue;}</style>',
        ],
    }
