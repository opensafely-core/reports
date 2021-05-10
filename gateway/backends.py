from urllib.parse import urljoin

import structlog
from django.conf import settings
from jose import jwk
from jose.exceptions import JWKError
from jose.utils import base64url_decode
from social_core.backends.open_id_connect import OpenIdConnectAuth


logger = structlog.getLogger()


class NHSIDConnectAuth(OpenIdConnectAuth):
    """
    Open ID Connect backend for NHS Identity
    """

    name = "nhsid"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.redirect_uri = urljoin(settings.BASE_URL, "auth")

    @property
    def OIDC_ENDPOINT(self):
        """OIDC_ENDPOINT as a property so tests can mock it"""
        return settings.SOCIAL_AUTH_NHSID_API_URL

    def auth_params(self, state=None):
        """
        Update auth params to prompt re-login

        Include the `prompt` param to require users to re-authenticate with NHS Identity
        even if already authenticated
        """
        params = super().auth_params(state)
        params.update({"prompt": "login"})
        return params

    def get_user_details(self, response):
        """Return user details from an NHS ID OpenID Connect request"""
        values = super().get_user_details(response)
        # Additional NHS person details (from the nhsperson scope)
        values["title"] = response.get("title")
        values["display_name"] = response.get("display_name", values["fullname"])
        # NHS organisation details (from the associatedorgs scope)
        values["nhsid_user_orgs"] = response.get("nhsid_user_orgs", [])
        return values

    def find_valid_key(self, id_token):
        try:
            return super().find_valid_key(id_token)
        except JWKError:
            for key in self.get_jwks_keys():
                # Here we go through all the keys retrieved from the jwks endpoint one
                # by one until we find one that can be verified.
                # NHS Identity's OIDC provider's jwks endpoint returns keys for
                # algorithms that jose doesn't currently support
                # However, NHS Identity always uses RS256 to sign JWTs unless
                # specifically requested to do otherwise, so we can just ignore key
                # construction failures.
                # Log the unsupported key as a warning in case we ever attempt to use an
                # unsupported algorithm in future.
                # The key construction is not wrapped in a try...except so that other,
                # legitimate errors will still be raised.
                if jwk.get_key(key["alg"]) is not None:
                    rsakey = jwk.construct(key)
                    message, encoded_sig = id_token.rsplit(".", 1)
                    decoded_sig = base64url_decode(encoded_sig.encode("utf-8"))
                    if rsakey.verify(message.encode("utf-8"), decoded_sig):
                        logger.info("Key verified", alg=key["alg"])
                        return key
                else:
                    logger.warning("Unsupported algorithm", alg=key["alg"])
