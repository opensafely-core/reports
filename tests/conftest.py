import logging
from os import environ
from pathlib import Path

import pytest
import responses
import structlog
from django.contrib.auth.models import Permission
from structlog.testing import LogCapture

from reports.models import Org

from .factories import UserFactory


@pytest.fixture
def user_with_permission():
    permission = Permission.objects.get(codename="view_draft")

    # set up a user with the view_draft permission
    user = UserFactory()
    user.user_permissions.add(permission)

    return user


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
def http_responses():
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        yield rsps


@pytest.fixture
def reset_environment_after_test():
    old_environ = dict(environ)
    yield
    environ.clear()
    environ.update(old_environ)


class MockRepo:
    def __init__(self, url):
        self.url = url

    def clear_cache(self): ...


@pytest.fixture
def mock_repo_url(mocker):
    def create_mock_repo(url):
        mocker.patch("reports.github.GithubReport.repo", MockRepo(url))

    return create_mock_repo


@pytest.fixture(autouse=True)
def skip_github_validation(reset_environment_after_test):
    environ["GITHUB_VALIDATION"] = "False"


@pytest.fixture
def bennett_org():
    # we add this in migrations so can rely on it here
    return Org.objects.get(slug="bennett")
