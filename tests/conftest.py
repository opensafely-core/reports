import json
import logging
from os import environ
from pathlib import Path

import django.db.models
import httpretty as _httpretty
import pytest
import structlog
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.sessions.middleware import SessionMiddleware
from django.core import management
from django.test import RequestFactory
from model_bakery import baker
from social_django.utils import load_strategy
from structlog.testing import LogCapture

from gateway.backends import NHSIDConnectAuth
from reports.github import GithubReport

from .gateway.mocks import OPENID_CONFIG


User = get_user_model()


@pytest.fixture
def user_with_permission():
    user = User.objects.create_user(username="user1", password="testpass")
    permission = Permission.objects.get(codename="view_draft")
    user.user_permissions.add(permission)
    yield user


@pytest.fixture
def user_no_permission():
    yield User.objects.create_user(username="user2", password="testpass")


@pytest.fixture
def researcher():
    management.call_command("ensure_groups")
    group = Group.objects.get(name="researchers")
    user = User.objects.create_user(username="researcher", password="testpass")
    user.groups.add(group)
    yield user


def remove_cache_file_if_exists():
    test_cache_path = Path(__file__).parent.parent / "test_cache.sqlite"
    if test_cache_path.exists():  # pragma: no cover
        test_cache_path.unlink()


def pytest_sessionstart(session):
    """
    Modify logging and clean up old test cache files before session starts

    requests_cache emits an annoying and unnecessary warning about unrecognised kwargs
    because we're using a custom cache name.  Set its log level to ERROR just for the tests
    """
    logger = logging.getLogger("requests_cache")
    logger.setLevel("ERROR")

    remove_cache_file_if_exists()


def pytest_sessionfinish(session, exitstatus):
    """clean up test cache files after session starts"""
    remove_cache_file_if_exists()  # pragma: no cover


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
    # As of Django 4, the `get_response` arg to SessionMiddleware (via MiddlewareMixin)
    # is required and can't be None.  SessionMiddleware never uses it, so it
    # doesn't matter what we give it here.
    SessionMiddleware(object()).process_request(request)
    strategy = load_strategy(request=request)

    httpretty.register_uri(
        httpretty.GET,
        backend.OIDC_ENDPOINT + "/.well-known/openid-configuration",
        status=200,
        body=json.dumps(OPENID_CONFIG),
    )

    return backend, strategy


@pytest.fixture
def reset_environment_after_test():
    old_environ = dict(environ)
    yield
    environ.clear()
    environ.update(old_environ)


class MockRepo:
    def __init__(self, url):
        self.url = url

    def clear_cache(self):
        ...


@pytest.fixture
def mock_repo_url(mocker):
    def create_mock_repo(url):
        mocker.patch("reports.github.GithubReport.repo", MockRepo(url))

    return create_mock_repo


@pytest.fixture(autouse=True)
def skip_github_validation(reset_environment_after_test):
    environ["GITHUB_VALIDATION"] = "False"


class MockGithubReport(GithubReport):
    def __init__(self, report, html):
        self.report = report
        self.html = html

    def get_html(self):
        return self.html


@pytest.fixture
def mock_github_report_with_html(mocker):
    def create_report(html):
        report = baker.make_recipe("reports.dummy_report")
        mock_report = MockGithubReport(report, html)
        return mock_report

    return create_report


baker.generators.add(
    "reports.models.AutoPopulatingCharField",
    baker.generators.default_mapping[django.db.models.CharField],
)
