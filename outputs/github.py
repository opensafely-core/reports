from base64 import b64decode
from datetime import datetime
from pathlib import Path

import requests
import requests_cache
from bs4 import BeautifulSoup, Tag
from django.utils.safestring import mark_safe
from environs import Env
from furl import furl


env = Env()


class GithubAPIException(Exception):
    ...


class GithubClient:
    """
    A connection to the Github API, using cached requests by default
    """

    user_agent = "OpenSAFELY Output Explorer"
    base_url = "https://api.github.com"

    def __init__(self, use_cache=True):
        token = env.str("GITHUB_TOKEN", None)
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": self.user_agent,
        }
        if token:
            self.headers["Authorization"] = f"token {env.str('GITHUB_TOKEN')}"
        if use_cache:
            self.session = requests_cache.CachedSession(
                backend="sqlite", namespace=env.str("REQUESTS_CACHE_NAME", "http_cache")
            )
        else:
            self.session = requests.Session()

    def _get_json(self, path_segments, **add_args):
        """
        Builds and calls a url from the base and path segments
        Returns the response as json
        """
        f = furl(self.base_url)
        f.path.segments += path_segments
        if add_args:
            f.add(add_args)
        response = self.session.get(f.url, headers=self.headers)

        # Report some expected errors
        if response.status_code == 403:
            errors = response.json()["errors"]
            for error in errors:
                if error["code"] == "too_large":
                    raise GithubAPIException("Error: File too large")
        elif response.status_code == 404:
            raise GithubAPIException(response.json()["message"])
        # raise any other unexpected status
        response.raise_for_status()
        response_json = response.json()
        return response_json

    def get_repo(self, owner_and_repo):
        """
        Ensure a repo exists and return a GithubRepo
        """
        owner, repo = owner_and_repo.split("/")
        repo_path_seqments = ["repos", owner, repo]
        # call it to raise exceptions in case it doesn't exist
        self._get_json(repo_path_seqments)
        return GithubRepo(self, owner, repo)


class GithubRepo:
    """
    Fetch contents of a Github Repo
    """

    def __init__(self, client, owner, name):
        self.client = client
        self.repo_path_segments = ["repos", owner, name]

    def get_contents(self, path, ref):
        """
        Fetch the contents of a path and ref (branch/commit/tag)

        Returns a single GithubContentFile if the path is a single file, or a list
        of GithubContentFiles if the path is a folder
        """
        path_segments = [*self.repo_path_segments, "contents", path]
        contents = self.client._get_json(path_segments, ref=ref)
        if isinstance(contents, list):
            return [GithubContentFile.from_json({**content}) for content in contents]

        contents["last_updated"] = self.get_last_updated(path, ref)
        return GithubContentFile.from_json(contents)

    def get_git_blob(self, sha, last_updated):
        """Fetch a git blob by sha"""
        path_segments = [*self.repo_path_segments, "git", "blobs", sha]
        response = self.client._get_json(path_segments)
        response["last_updated"] = last_updated
        return GithubContentFile.from_json(response)

    def get_commits_for_file(self, path, ref):
        path_segments = [*self.repo_path_segments, "commits"]
        response = self.client._get_json(path_segments, sha=ref, path=path)
        return response

    def get_last_updated(self, path, ref):
        commits = self.get_commits_for_file(path, ref)
        last_commit_date = commits[0]["commit"]["committer"]["date"]
        return datetime.strptime(last_commit_date, "%Y-%m-%dT%H:%M:%SZ").date()


class GithubContentFile:
    """Holds information about a single file in a repo"""

    def __init__(self, name, last_updated, content, sha):
        self.name = name
        self.last_updated = last_updated
        self.content = content
        self.sha = sha

    @classmethod
    def from_json(cls, json_input):
        return cls(
            name=json_input.get("name"),
            content=json_input.get("content"),
            last_updated=json_input.get("last_updated"),
            sha=json_input["sha"],
        )

    @property
    def decoded_content(self):
        # self.content may be None when /contents has returned a list of files
        if self.content:
            return b64decode(self.content).decode("utf-8")


class GitHubOutput:
    """
    A class for interacting with a Github repo and html file associated with a single
    Output instance
    """

    def __init__(self, output, repo=None, use_cache=True):
        self.client = GithubClient(use_cache=use_cache)
        self.output = output
        self._repo = repo

    @property
    def repo(self):
        if self._repo is None:
            self._repo = self.client.get_repo(f"opensafely/{self.output.repo}")
        return self._repo

    def get_parent_contents(self):
        parent_folder = str(Path(self.output.output_html_file_path).parent)
        return self.repo.get_contents(parent_folder, ref=self.output.branch)

    def matching_output_file_from_parent_contents(self):
        output_html_file_name = Path(self.output.output_html_file_path).name
        return (
            content_file
            for content_file in self.get_parent_contents()
            if content_file.name == output_html_file_name
        )

    def get_contents_from_git_blob(self):
        """
        Get all the content files from the parent folder (doesn't download the actual content
        itself, but returns a list of GithubContentFile objects, from which we can obtain sha for
        the relevant file), retrieve the git blob and return it as a GithubContentFile
        """
        # Find the file in the parent folder whose name matches the output file we want
        matching_content_file = next(self.matching_output_file_from_parent_contents())
        last_updated = self.repo.get_last_updated(
            self.output.output_html_file_path, self.output.branch
        )
        blob = self.repo.get_git_blob(matching_content_file.sha, last_updated)
        return blob

    def get_html(self):
        """
        Fetches an output html file (an exported jupyter notebook) from a github repo based
        on `output`, an Output model instance.
        The notebook html consists of style, body and script tags.  Ignores any script tags.
        Return the style tags and html body content for display in template.
        """
        if self.output.use_git_blob:
            contents = self.get_contents_from_git_blob()
        else:
            try:
                contents = self.repo.get_contents(
                    self.output.output_html_file_path, ref=self.output.branch
                )

            except GithubAPIException:
                # If the single file was too big (>1Mb), we get an exception.  Get the git blob
                # and retrieve the contents from there instead
                contents = self.get_contents_from_git_blob()
                self.output.use_git_blob = True
                self.output.save()

        if self.output.last_updated != contents.last_updated:
            self.output.last_updated = contents.last_updated
            self.output.save()

        # Reports may be formatted as proper HTML documents, or just as fragments of HTML. In the former case we want
        # just the body, in the latter we want the whole thing.
        soup = BeautifulSoup(contents.decoded_content, "html.parser")
        html = soup.find("html") or soup  # in case we get an <html> tag but no <body>
        body = html.find("body") or html

        html_content = []
        for content in body.contents:
            if isinstance(content, Tag):
                if content.name in ["script", "style"]:
                    continue
                html_content.append(content.decode())
            else:
                html_content.append(content)

        return {"body": mark_safe("".join(html_content).strip())}
