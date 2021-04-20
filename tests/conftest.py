import json

import httpretty as _httpretty
import pytest
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory
from social_django.utils import load_strategy

from gateway.backends import NHSIDConnectAuth

from .mocks import OPENID_CONFIG


@pytest.fixture
def mock_settings(settings):
    settings.SOCIAL_AUTH_NHSID_KEY = "dummy-client-id"
    settings.SOCIAL_AUTH_NHSID_SECRET = "dummy-secret"
    settings.SOCIAL_AUTH_NHSID_API_URL = "https://dummy-nhs.net/oidc"


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
