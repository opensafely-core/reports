import json

import pytest
import requests

from reports.github_client import GithubClient, GithubException


def test_get_sends_headers_and_query_parameters(httpretty):
    httpretty.register_uri(
        httpretty.GET,
        "https://api.github.com/repos/opensafely/test/contents?ref=main",
        status=200,
        body="response",
    )

    client = GithubClient(use_cache=False, token="test-token")
    response = client.get(
        ["repos", "opensafely", "test", "contents"],
        client.headers,
        ref="main",
    )

    assert response.status_code == 200
    assert response.text == "response"
    assert (
        httpretty.last_request().headers["Accept"] == "application/vnd.github.v3+json"
    )
    assert httpretty.last_request().headers["Authorization"] == "token test-token"
    assert httpretty.last_request().querystring == {"ref": ["main"]}


def test_get_returns_error_response(httpretty):
    httpretty.register_uri(
        httpretty.GET,
        "https://api.github.com/repos/opensafely/missing",
        status=404,
        body=json.dumps({"message": "Not Found"}),
    )

    client = GithubClient(use_cache=False)
    response = client.get(
        ["repos", "opensafely", "missing"],
        client.headers,
    )

    assert response.status_code == 404
    assert response.json()["message"] == "Not Found"


def test_get_json_returns_decoded_response(httpretty):
    httpretty.register_uri(
        httpretty.GET,
        "https://api.github.com/repos/opensafely/test",
        status=200,
        body=json.dumps({"name": "test"}),
    )

    client = GithubClient(use_cache=False)

    assert client.get_json(["repos", "opensafely", "test"]) == {"name": "test"}


def test_get_json_raises_for_rate_limit(httpretty):
    httpretty.register_uri(
        httpretty.GET,
        "https://api.github.com/repos/opensafely/test",
        status=403,
        body=json.dumps({"message": "API rate limit exceeded"}),
    )

    client = GithubClient(use_cache=False)

    with pytest.raises(GithubException, match="API rate limit exceeded"):
        client.get_json(["repos", "opensafely", "test"])


def test_get_json_raises_for_unexpected_http_error(httpretty):
    httpretty.register_uri(
        httpretty.GET,
        "https://api.github.com/repos/opensafely/test",
        status=500,
        body=json.dumps({"message": "Server error"}),
    )

    client = GithubClient(use_cache=False)

    with pytest.raises(requests.HTTPError):
        client.get_json(["repos", "opensafely", "test"])


def test_get_repo(httpretty):
    httpretty.register_uri(
        httpretty.GET,
        "https://api.github.com/repos/opensafely/test",
        status=200,
        body=json.dumps({"description": "A test repository"}),
    )

    client = GithubClient(use_cache=False)
    repo = client.get_repo("opensafely", "test")

    assert repo.owner == "opensafely"
    assert repo.name == "test"
    assert repo.about == "A test repository"


def test_get_repo_not_found(httpretty):
    httpretty.register_uri(
        httpretty.GET,
        "https://api.github.com/repos/opensafely/missing",
        status=404,
        body=json.dumps({"message": "Not Found"}),
    )

    client = GithubClient(use_cache=False)

    with pytest.raises(GithubException, match="Not Found"):
        client.get_repo("opensafely", "missing")


def test_client_without_token(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    client = GithubClient(use_cache=False)

    assert "Authorization" not in client.headers
