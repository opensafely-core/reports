import requests
import requests_cache
from environs import Env


env = Env()


class JobServerClient:
    """
    A connection to the Jobs site

    Optionally uses request caching

    Attributes:
        user_agent (str): set from JOB_SERVER_USER_AGENT environment variable;
        a string to identify the application
        use_cache (bool): whether to use request caching; defaults to False
        token (str): optional authentication token
        expire_after (int): For cached requests, set a global expiry for the session (default = -1; never expires)
        urls_expire_after (dict): Set expiry on specific url patterns (falls back to `expire_after` if no match found), e.g.
            urls_expire_after = {
                '*/pulls': 60,  # expire requests to get pull requests after 60 secs
                '*/branches': 60 * 5, # expire requests to get branches after 5 mins
                '*/commits': 30,  # expire requests to get commits after 30 secs
            }
    """

    cache_name = env.str("REQUESTS_CACHE_NAME", default="http_cache")
    user_agent = env.str("JOB_SERVER_USER_AGENT", default="reports")

    def __init__(
        self, use_cache=False, token=None, expire_after=-1, urls_expire_after=None
    ):
        if use_cache:
            self.session = requests_cache.CachedSession(
                backend="sqlite",
                cache_name=self.cache_name,
                expire_after=expire_after,
                urls_expire_after=urls_expire_after,
            )
        else:
            self.session = requests.Session()

        # always set a token, even if we're getting published outputs to simply
        # the code on either side.
        token = token or env.str("JOB_SERVER_TOKEN", default=None)
        self.session.headers = {
            "User-Agent": self.user_agent,
            "Authorization": token,
        }

    def file_exists(self, url):
        return self.session.head(url, allow_redirects=True).ok

    def get_file(self, url):
        r = self.session.get(url, allow_redirects=True, timeout=1)
        r.raise_for_status()

        # TODO: need to get the last_updated value here too
        return r.text


class JobServerReport:
    """
    A class for interacting with an HTML file associated with a single Report
    instance, hosted as an output on the Jobs site.
    """

    def __init__(self, report, use_cache=True):
        self.client = JobServerClient(use_cache=use_cache)
        self._fetched_html = None

    def file_exists(self):
        return self.client.file_exists(self.report.job_server_url)

    def get_html(self):
        """
        Fetches a report html file (an exported jupyter notebook) from a
        job-server output URL based on `report`, a Report model instance.
        """
        if self._fetched_html is not None:
            return self._fetched_html

        file = self.client.get_file(self.report.job_server_url)

        # if self.report.last_updated != file.last_updated:
        #     self.report.last_updated = file.last_updated
        #     self.report.save()

        self._fetched_html = file

        return self._fetched_html
