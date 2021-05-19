import json

import httpretty as _httpretty
import pytest
import structlog
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory
from social_django.utils import load_strategy
from structlog.testing import LogCapture

from gateway.backends import NHSIDConnectAuth
from outputs.github import GithubContentFile

from .gateway.mocks import OPENID_CONFIG


@pytest.fixture(name="log_output", scope="module")
def fixture_log_output():
    return LogCapture()


@pytest.fixture(autouse=True)
def fixture_configure_structlog(log_output):
    structlog.configure(processors=[log_output])


@pytest.fixture
def httpretty():
    _httpretty.reset()
    _httpretty.enable()
    yield _httpretty
    _httpretty.disable()


@pytest.fixture
def mock_backend_and_strategy(httpretty):
    backend = NHSIDConnectAuth()
    request_factory = RequestFactory()
    request = request_factory.get("/", data={"x": "1"})
    SessionMiddleware(lambda: None).process_request(request)
    strategy = load_strategy(request=request)

    httpretty.register_uri(
        httpretty.GET,
        backend.OIDC_ENDPOINT + "/.well-known/openid-configuration",
        status=200,
        body=json.dumps(OPENID_CONFIG),
    )

    return backend, strategy


@pytest.fixture
def mock_repo(mocker):
    """Mock a PyGitHub Repo and its methods"""

    def create_repo(**kwargs):
        repo = mocker.Mock()
        exception = kwargs.get("get_contents_exception", [])

        def _content_file(name):
            return GithubContentFile(
                name=name,
                sha="foo",
                last_modified="Tue, 27 Apr 2021 10:00:00 GMT",
                content=None,
            )

        content_files = [
            _content_file(content_file_name)
            for content_file_name in kwargs.get("content_files", [])
        ]
        if content_files:
            contents = [exception, *([content_files] * 2)]
            repo.get_contents = mocker.MagicMock(
                side_effect=contents, __iter__=content_files
            )

        else:
            repo.get_contents = mocker.Mock(
                return_value=GithubContentFile(
                    name="foo",
                    sha="foo",
                    last_modified="Tue, 27 Apr 2021 10:00:00 GMT",
                    content=kwargs.get("contents"),
                )
            )

        repo.get_git_blob = mocker.Mock(
            side_effect=[
                GithubContentFile(
                    name="foo",
                    sha="foo",
                    last_modified="Tue, 27 Apr 2021 10:00:00 GMT",
                    content=kwargs.get("blob"),
                )
            ]
            * 2
        )
        return repo

    return create_repo
