from environs import Env
from osgithub import GithubClient


env = Env()


class GithubReport:
    """
    A class for interacting with a Github repo and html file associated with a single
    Report instance
    """

    def __init__(self, report, repo=None, use_cache=True):
        self.client = GithubClient(use_cache=use_cache)
        self.report = report
        self._repo = repo
        self._fetched_html = None

    @property
    def repo(self):
        if self._repo is None:
            self._repo = self.client.get_repo("opensafely", self.report.repo)
        return self._repo

    def file_exists(self):
        if (
            self.repo.get_matching_file_from_parent_contents(
                self.report.report_html_file_path, self.report.branch
            )
            is None
        ):
            return False
        return True

    def get_parent_contents(self):
        return self.repo.get_parent_contents(
            self.report.report_html_file_path, self.report.branch
        )

    def get_html(self):
        """
        Fetches a report html file (an exported jupyter notebook) from a github repo based
        on `report`, a Report model instance.
        """
        if self._fetched_html is None:
            if self.report.use_git_blob:
                file = self.repo.get_contents(
                    self.report.report_html_file_path,
                    self.report.branch,
                    from_git_blob=True,
                )
            else:
                file, fetch_type = self.repo.get_contents(
                    self.report.report_html_file_path,
                    ref=self.report.branch,
                    return_fetch_type=True,
                )
                if fetch_type == "blob":
                    self.report.use_git_blob = True
                    self.report.save()

            # convert to a date for Report.last_updated
            github_last_updated = file.last_updated.date()
            if self.report.last_updated != github_last_updated:
                self.report.last_updated = github_last_updated
                self.report.save()

            self._fetched_html = file.decoded_content
        return self._fetched_html

    def last_updated(self):
        """
        Return the last updated date separately to the fully processed HTML
        """
        self.get_html()
        # last_updated is the only field on a Report instance that is retrieved from GitHub (rather
        # than being entered manually in the Report admin). As it is rendered in the template before
        # the processed html content, we need to be have refreshed the fetched GitHub data at the
        # point that the field it rendered, otherwise the pre-fetched (possibly stale) date will be
        # rendered and cached in the template.
        return self.report.last_updated
