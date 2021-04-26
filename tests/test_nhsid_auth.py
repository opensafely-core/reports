import base64
import json
from calendar import timegm
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import urlparse

import pytest
import requests
from django.conf import settings as django_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from jose import jwt
from social_core.exceptions import AuthTokenError
from social_core.utils import parse_qs, url_add_parameters
from social_django.models import Association
from social_django.strategy import DjangoStrategy

from gateway.backends import NHSIDConnectAuth
from gateway.models import Organisation

from .mocks import JWK_KEY, JWK_PUBLIC_KEY

User = get_user_model()


@dataclass
class AuthTestOptions:
    """Convenience class for auth options in tests"""

    backend: NHSIDConnectAuth
    strategy: DjangoStrategy
    user_data_body: Optional[dict] = None
    jwk_keys: Optional[list] = None
    # The following are options for testing invalid tokens
    nonce: Optional[str] = None
    token_expiry_datetime: Optional[datetime] = None
    access_token: str = "dummy-access-token"
    access_token_status: int = 200
    tampered: bool = False
    issuer: Optional[str] = None
    issue_time: Optional[datetime] = None
    audience: Optional[str] = None


def assert_user_attributes(user, expected):
    for user_attribute, expected_attribute in expected["user"].items():
        assert getattr(user, user_attribute) == expected_attribute
    organisations = list(user.organisations.values_list("name", flat=True))
    assert Organisation.objects.count() == len(organisations)
    assert (
        list(str(organisation) for organisation in user.organisations.all())
        == expected["organisations"]
    )


def do_auth(httpretty, start_url, auth_options, access_token_body):
    """
    Mock all the relevant uris for auth
    Return the target url with the expected code, nonce, redirect uri and params
    """
    complete_url = reverse("gateway:nhsid_complete")
    start_query = parse_qs(urlparse(start_url).query)
    target_url = auth_options.strategy.build_absolute_uri(complete_url)
    target_url = url_add_parameters(target_url, {"state": start_query["state"]})

    # mock the authorization call and its redirect to the target_url
    httpretty.register_uri(httpretty.GET, start_url, status=301, location=target_url)
    httpretty.register_uri(httpretty.GET, target_url, status=200, body="foobar")

    # Mock the JWK keys request (used to validate JWT id_token)
    httpretty.register_uri(
        httpretty.GET,
        auth_options.backend.jwks_uri(),
        status=200,
        body=json.dumps({"keys": auth_options.jwk_keys or [JWK_PUBLIC_KEY]}),
    )
    # Mock the call to get the access token
    httpretty.register_uri(
        httpretty.POST,
        uri=auth_options.backend.access_token_url(),
        status=auth_options.access_token_status,
        body=json.dumps(access_token_body) or "",
        content_type="text/json",
    )
    # Mock the call to the userinfo url
    httpretty.register_uri(
        httpretty.GET,
        auth_options.backend.userinfo_url(),
        body=json.dumps(auth_options.user_data_body) or "",
        content_type="text/json",
    )
    return target_url


def prepare_id_token(nonce, auth_options):
    # Prepare the id_token (JWT) for the access token request
    issue_time = auth_options.issue_time or datetime.utcnow()
    iat = timegm(issue_time.utctimetuple())
    expiry_datetime = (
        auth_options.token_expiry_datetime or datetime.utcnow() + timedelta(seconds=300)
    )
    claims = {
        "iss": auth_options.issuer or django_settings.SOCIAL_AUTH_NHSID_API_URL,
        "nonce": nonce,
        "aud": auth_options.audience or django_settings.SOCIAL_AUTH_NHSID_KEY,
        "azp": django_settings.SOCIAL_AUTH_NHSID_SECRET,
        "exp": timegm(expiry_datetime.utctimetuple()),
        "iat": iat,
        "sub": "1234",
    }
    id_token = jwt.encode(
        claims=claims,
        key={**JWK_KEY, "iat": iat, "nonce": nonce},
        algorithm="RS256",
        access_token=auth_options.access_token,
    )
    if auth_options.tampered:
        # tamper with the token
        header, msg, sig = id_token.split(".")
        claims["sub"] = "1235"
        msg = base64.encodebytes(json.dumps(claims).encode()).decode()
        id_token = ".".join([header, msg, sig])
    return id_token


def do_start(httpretty, auth_options):
    """
    Do all the things to setup the authentication but don't actually complete it.
    - generate code, state, nonce and call authorization url
    - build target url
    - request access token, mock JWT signation verification request
    - mock userinfo request
    Return the expected request data
    """
    # backend.start() generates the nonce and creates the Association
    start_url = auth_options.backend.start().url
    assert Association.objects.count() == 1

    # set up the mocked auth requests
    nonce = auth_options.nonce or Association.objects.first().handle
    access_token_body = {
        "access_token": auth_options.access_token,
        "token_type": "bearer",
        "id_token": prepare_id_token(nonce, auth_options),
    }
    target_url = do_auth(httpretty, start_url, auth_options, access_token_body)

    # Now that the auth is all set up, get the start url. `requests` will follow the
    # redirect, so the response text is the body from the mock target url
    response = requests.get(start_url)
    assert response.url == target_url
    assert response.text == "foobar"

    # format the expected request data from the start and target urls
    request_data = parse_qs(urlparse(start_url).query)
    target_request_data = parse_qs(urlparse(target_url).query)
    request_data.update(target_request_data)
    return request_data


def do_login(httpretty, auth_options):
    """
    Set up all relevant mocked uris for authentication and complete the login
    Return the logged in user
    """
    request_data = do_start(httpretty, auth_options)
    backend = auth_options.backend
    backend.data = request_data
    # Complete the login - this validates the JWT key, validates the various claims and
    # calls the userinfo endpoint
    return backend.complete()


def do_client_login(test_client, httpretty, auth_options):
    """
    Set up all relevant mocked uris for authentication
    Set the expected state on the test client's session and call the callback url via
    the test client
    """
    request_data = do_start(httpretty, auth_options)
    # set the expected state value in the test Client's session to match the
    # value in the callback url
    state = request_data["state"]
    session = test_client.session
    session["nhsid_state"] = state
    session.save()

    # Finally, call the complete url with the code and state
    callback_url = reverse("gateway:nhsid_complete") + f"?code=dummy-code&state={state}"
    test_client.get(callback_url, follow=False, secure=True)


@pytest.mark.django_db
def test_nhsid_backend_complete(httpretty, mock_settings, mock_backend_and_strategy):
    """
    Test logging in a new user
    """
    # Make sure we're using dummy settings
    assert django_settings.SOCIAL_AUTH_NHSID_KEY == "dummy-client-id"
    assert User.objects.exists() is False
    assert Organisation.objects.exists() is False
    # The Association is the OpenID Connect association, and is generated and stored with the nonce
    # when the authorization_url is called
    assert Association.objects.exists() is False

    # Do the login with the dummy settings and the user data for this test
    # user_data_body is the expected response from the NHS ID /userinfo endpoint
    user_data_body = {"sub": 1, "name": "Test User", "nhsid_useruid": "test"}
    backend, strategy = mock_backend_and_strategy
    auth_options = AuthTestOptions(
        backend=backend, strategy=strategy, user_data_body=user_data_body
    )
    user = do_login(httpretty, auth_options)
    user.refresh_from_db()
    expected = {
        "user": {
            "username": "test",
            "first_name": "",
            "last_name": "",
            "email": "",
            "title": None,
            "display_name": "Test User",
        },
        "organisations": [],
    }
    assert_user_attributes(user, expected)


@pytest.mark.django_db
def test_unsupported_algorithm(httpretty, mock_settings, mock_backend_and_strategy):
    assert User.objects.exists() is False
    user_data_body = {"sub": 1, "name": "Test User", "nhsid_useruid": "test"}
    backend, strategy = mock_backend_and_strategy
    # Mock the keys returned from the JWKS uri to include an unsupported algorithm
    # before the supported one; the unsupported algorithm will be tried first and
    # should not raise an error
    unsupported = dict(JWK_PUBLIC_KEY)
    unsupported["alg"] = "UNK"
    auth_options = AuthTestOptions(
        backend=backend,
        strategy=strategy,
        user_data_body=user_data_body,
        jwk_keys=[unsupported, JWK_PUBLIC_KEY],
    )
    user = do_login(httpretty, auth_options)
    assert user.username == "test"


@pytest.mark.django_db
def test_no_supported_algorithms(httpretty, mock_settings, mock_backend_and_strategy):
    assert User.objects.exists() is False
    user_data_body = {"sub": 1, "name": "Test User", "nhsid_useruid": "test"}
    backend, strategy = mock_backend_and_strategy
    # Mock the keys returned from the JWKS uri so that no algorithms returned are
    # supported
    unsupported = dict(JWK_PUBLIC_KEY)
    unsupported["alg"] = "UNK"
    auth_options = AuthTestOptions(
        backend=backend,
        strategy=strategy,
        user_data_body=user_data_body,
        jwk_keys=[unsupported],
    )
    with pytest.raises(
        AuthTokenError, match="Token error: Signature verification failed"
    ):
        do_login(httpretty, auth_options)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "auth_option_kwargs,expected_error",
    [
        (
            {"token_expiry_datetime": datetime.utcnow() - timedelta(600)},
            "Signature has expired",
        ),
        ({"tampered": True}, "Signature verification failed"),
        ({"nonce": "dud-nonce"}, "Incorrect id_token: nonce"),
        ({"issuer": "http://fake"}, "Invalid issuer"),
        ({"issue_time": datetime.utcnow() - timedelta(60)}, "Incorrect id_token: iat"),
        ({"audience": "another-audience"}, "Invalid audience"),
    ],
    ids=[
        "test_nhsid_backend_expired_signature",
        "test_nhsid_backend_invalid_signature",
        "test_nhsid_backend_invalid_nonce",
        "test_nhsid_backend_invalid_issuer",
        "test_nhsid_backend_invalid_issue_time",
        "test_nhsid_backend_invalid_audience",
    ],
)
def test_nhsid_backend_token_errors(
    httpretty,
    mock_settings,
    mock_backend_and_strategy,
    auth_option_kwargs,
    expected_error,
):
    """
    Test the various possible invalid tokens and claims.
    This runs the same checks that python-social-auth runs on the base OpenIdConnectAuth
    """
    assert User.objects.exists() is False
    backend, strategy = mock_backend_and_strategy
    auth_options = AuthTestOptions(
        backend=backend, strategy=strategy, **auth_option_kwargs
    )
    with pytest.raises(AuthTokenError, match=f"Token error: {expected_error}"):
        do_login(httpretty, auth_options)
    assert User.objects.exists() is False


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_data,expected",
    [
        (
            {"sub": 1, "name": "Test User", "nhsid_useruid": "test"},
            {
                "user": {
                    "username": "test",
                    "first_name": "",
                    "last_name": "",
                    "email": "",
                    "title": None,
                    "display_name": "Test User",
                },
                "organisations": [],
            },
        ),
        (
            {
                "sub": 1,
                "name": "Test User1",
                "display_name": "Testy",
                "nhsid_useruid": "test1",
                "title": "Dr",
            },
            {
                "user": {
                    "username": "test1",
                    "first_name": "",
                    "last_name": "",
                    "email": "",
                    "title": "Dr",
                    "display_name": "Testy",
                },
                "organisations": [],
            },
        ),
        (
            {
                "sub": 1,
                "name": "Test User2",
                "nhsid_useruid": "test2",
                "title": "Dr",
                "nhsid_user_orgs": [{"org_code": "ORG-123", "org_name": "Test org"}],
            },
            {
                "user": {
                    "username": "test2",
                    "first_name": "",
                    "last_name": "",
                    "email": "",
                    "title": "Dr",
                    "display_name": "Test User2",
                },
                "organisations": ["ORG-123 - Test org"],
            },
        ),
        (
            {
                "sub": 1,
                "name": "Test User3",
                "family_name": "User3",
                "given_name": "Test",
                "display_name": "Dr Test User3",
                "nhsid_useruid": "test3",
                "title": "Dr",
                "nhsid_user_orgs": [
                    {"org_code": "ORG-123", "org_name": "Test org"},
                    {"org_code": "ORG-456", "org_name": "Test org 1"},
                ],
            },
            {
                "user": {
                    "username": "test3",
                    "first_name": "Test",
                    "last_name": "User3",
                    "email": "",
                    "title": "Dr",
                    "display_name": "Dr Test User3",
                },
                "organisations": ["ORG-123 - Test org", "ORG-456 - Test org 1"],
            },
        ),
    ],
    ids=[
        "1. Test minimal user data: display name is generated from name; missing data is dealt with",
        "2. Test display name is generated from display_name value if provided",
        "3. Test organisation created and assigned it to the new user",
        "4. Test multiple organisations",
    ],
)
def test_login_new_user(
    client, httpretty, mock_settings, mock_backend_and_strategy, user_data, expected
):
    """
    Test that the pipeline creates a new user with relevant user data provided by NHS Identity.
    After a user is authenticated with NHS Identity, we request user data, specifically for the
    `nhsperson` and `associatedorgs` scopes, which return user data which we use to update the
    User, UserProfile and Organisation models.
    """
    # Make sure we're using dummy settings
    assert django_settings.SOCIAL_AUTH_NHSID_KEY == "dummy-client-id"
    assert User.objects.exists() is False
    assert Organisation.objects.exists() is False

    backend, strategy = mock_backend_and_strategy
    auth_options = AuthTestOptions(
        backend=backend, strategy=strategy, user_data_body=user_data
    )
    do_client_login(client, httpretty, auth_options)

    # A new user has been created with the expected attributes
    assert User.objects.count() == 1
    user = User.objects.first()
    assert user.is_active
    assert user.is_staff is False
    assert user.is_superuser is False
    assert_user_attributes(user, expected)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_data,expected_organisations",
    [
        (
            {
                "sub": 1,
                "name": "Test User",
                "nhsid_useruid": "test",
                "nhsid_user_orgs": [{"org_code": "ORG1", "org_name": "Org 1"}],
            },
            ["ORG1 - Org 1"],
        ),
        (
            {
                "sub": 2,
                "name": "Test User",
                "nhsid_useruid": "test",
                "nhsid_user_orgs": [
                    {"org_code": "ORG1", "org_name": "Org 1"},
                    {"org_code": "ORG2", "org_name": "Org 2"},
                ],
            },
            ["ORG1 - Org 1", "ORG2 - Org2"],
        ),
    ],
)
def test_login_existing_organisation(
    client,
    httpretty,
    mock_settings,
    mock_backend_and_strategy,
    user_data,
    expected_organisations,
):
    """
    Test that existing matching organisations are assigned to the new user
    """
    # Make sure we're using dummy settings
    assert django_settings.SOCIAL_AUTH_NHSID_KEY == "dummy-client-id"
    assert User.objects.exists() is False
    existing_organisation = Organisation.objects.create(name="Org 1", code="ORG1")
    assert Organisation.objects.count() == 1

    # Do the login with the dummy settings and the user data for this test
    # user_data is the expected response from the NHS ID /userinfo endpoint
    backend, strategy = mock_backend_and_strategy
    auth_options = AuthTestOptions(
        backend=backend, strategy=strategy, user_data_body=user_data
    )
    do_client_login(client, httpretty, auth_options)

    # A new user has been created
    assert User.objects.count() == 1
    user = User.objects.first()

    # New Organisations are only created if they don't already exist
    assert (
        user.organisations.count()
        == len(expected_organisations)
        == Organisation.objects.count()
    )
    assert existing_organisation in user.organisations.all()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "initial_user_data,initial_expected,updated_user_data,updated_expected",
    [
        (
            {
                "sub": 1,
                "name": "Test User",
                "given_name": "Test",
                "family_name": "User",
                "nhsid_useruid": "test1",
            },
            {
                "user": {
                    "first_name": "Test",
                    "last_name": "User",
                    "username": "test1",
                    "email": "",
                    "title": None,
                    "display_name": "Test User",
                },
                "organisations": [],
            },
            {
                "sub": 1,
                "name": "New Name",
                "given_name": "New",
                "family_name": "Name",
                "display_name": "Testy",
                "nhsid_useruid": "test1",
                "title": "Dr",
            },
            {
                "user": {
                    "username": "test1",
                    "first_name": "New",
                    "last_name": "Name",
                    "email": "",
                    "title": "Dr",
                    "display_name": "Testy",
                },
                "organisations": [],
            },
        ),
    ],
)
def test_login_existing_user(
    client,
    httpretty,
    mock_settings,
    mock_backend_and_strategy,
    initial_user_data,
    initial_expected,
    updated_user_data,
    updated_expected,
):
    """
    Test that the pipeline updates an existing user with relevant user data provided by NHS Identity.
    """
    # Make sure we're using dummy settings
    assert django_settings.SOCIAL_AUTH_NHSID_KEY == "dummy-client-id"

    assert User.objects.exists() is False
    assert Organisation.objects.exists() is False

    # Login with the initial user_data to create the user
    backend, strategy = mock_backend_and_strategy
    auth_options = AuthTestOptions(
        backend=backend, strategy=strategy, user_data_body=initial_user_data
    )
    do_client_login(client, httpretty, auth_options)

    # A new user has been created with the expected attributes
    assert User.objects.count() == 1
    user = User.objects.first()
    assert_user_attributes(user, initial_expected)

    client.logout()
    # Login again with the updated user_data
    auth_options = AuthTestOptions(
        backend=backend, strategy=strategy, user_data_body=updated_user_data
    )
    do_client_login(client, httpretty, auth_options)

    # No additional user created on second login.  Existing user has been updated with the new attributes
    assert User.objects.count() == 1
    assert User.objects.first().id == user.id
    user.refresh_from_db()
    assert_user_attributes(user, updated_expected)
