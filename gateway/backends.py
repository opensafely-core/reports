from urllib.parse import urljoin

from django.conf import settings
from social_core.backends.open_id_connect import OpenIdConnectAuth


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
