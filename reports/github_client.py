import json
from os import environ

import requests
import requests_cache
from furl import furl
from osgithub import GithubRepo


class GithubException(Exception):
    """An error accessing a report's GitHub source."""


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

    def get(self, path_segments, headers, **params):
        """
        Send a GET request to the GitHub API.

        Args:
            path_segments (list of str): segments of path after the base url
            headers: headers to pass to the request
            **params: any querystring args to be added (k=v pairs)

        Returns: HTTP Response
        """
        url = furl(self.base_url)
        url.path.segments += path_segments
        if params:
            url.add(params)

        return self.session.get(url.url, headers=headers)

    def get_json(self, path_segments, **params):
        """
        Fetch JSON data from the GitHub API.

        Args:
            path_segments (list of str): segments of path after the base url
            **params: optional querystring args to be added (k=v pairs)

        Returns:
            The decoded JSON response

        Raises:
            GithubException
        """
        response = self.get(path_segments, self.headers, **params)

        # Report some expected errors
        if response.status_code == 403 and "errors" not in response.json():
            raise GithubException(json.dumps(response.json()))

        if response.status_code == 404:
            raise GithubException(response.json()["message"])

        # raise any other unexpected status
        response.raise_for_status()
        return response.json()

    def get_repo(self, owner, name):
        """
        Look up a repository on GitHub.

        Args:
            owner (str): The repository owner
            name (str): The repository name

        Returns:
            A GithubRepo for the requested repository.
        """
        response = self.get_json(["repos", owner, name])
        return GithubRepo(self, owner, name, about=response["description"])
