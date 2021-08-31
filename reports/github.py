from bs4 import BeautifulSoup
from django.utils.safestring import mark_safe
from environs import Env
from lxml.html.clean import Cleaner
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

        if self.report.last_updated != file.last_updated:
            self.report.last_updated = file.last_updated
            self.report.save()

        return file.decoded_content

    def process_html(self):
        html = self.get_html()
        # We want to handle complete HTML documents and also fragments. We're going to extract the contents of the body
        # at the end of this function, but it's easiest to normalize to complete documents because that's what the
        # HTML-wrangling libraries we're using are most comfortable handling.
        if "<html>" not in html:
            html = f"<html><body>{html}</body></head>"

        cleaned = Cleaner(
            page_structure=False, style=True, kill_tags=["head"]
        ).clean_html(html)

        soup = BeautifulSoup(cleaned, "html.parser")

        # For small screens we want to allow side-scrolling for just a small number of elements. To enable this each one
        # needs to be wrapped in a div that we can target for styling.
        for tag in ["table", "pre"]:
            for element in soup.find_all(tag):
                element.wrap(soup.new_tag("div", attrs={"class": "overflow-wrapper"}))

        body_content = "".join([str(element) for element in soup.body.contents])
        return mark_safe(body_content)
