from os import environ

import requests
import requests_cache


class GithubClient:
    """A connection to the Github API, optionally uses request caching"""

    # Set from GITHUB_USER_AGENT environment variable; a string to identify the application
    user_agent = environ.get("GITHUB_USER_AGENT", "")
    # The base github api url
    base_url = "https://api.github.com"

    def __init__(
        self, use_cache=False, token=None, expire_after=-1, urls_expire_after=None
    ):
        """
        Args:
            use_cache (bool): whether to use request caching; defaults to False
            token (str): GitHub token. Optional; required to access private repos and avoid anonymous rate-limiting
            expire_after (int): For cached requests, set a global expiry for the session (default = -1; never expires)
            urls_expire_after (dict): Set expiry on specific url patterns (falls back to `expire_after` if no match found), e.g.
            urls_expire_after = {
                '*/pulls': 60,  # expire requests to get pull requests after 60 secs
                '*/branches': 60 * 5, # expire requests to get branches after 5 mins
                '*/commits': 30,  # expire requests to get commits after 30 secs
            }
        """

        token = token or environ.get("GITHUB_TOKEN", None)

        # Sets headers with token if provided and initialises session
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": self.user_agent,
        }
        if token:
            self.headers["Authorization"] = f"token {token}"

        if use_cache:
            self.session = requests_cache.CachedSession(
                backend="sqlite",
                cache_name=environ.get("REQUESTS_CACHE_NAME", "http_cache"),
                expire_after=expire_after,
                urls_expire_after=urls_expire_after,
            )
        else:
            self.session = requests.Session()
