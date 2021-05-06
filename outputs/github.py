from base64 import b64decode
from datetime import datetime
from pathlib import Path

from bs4 import BeautifulSoup, Tag
from django.utils.safestring import mark_safe
from environs import Env
from github import Github, GithubException


env = Env()


def get_repo(output):
    token = env.str("GITHUB_TOKEN", None)
    github_client = Github(token) if token else Github()
    repo = github_client.get_repo(f"opensafely/{output.repo}")
    return repo


def get_parent_contents(repo, output):
    parent_folder = str(Path(output.output_html_file_path).parent)
    return repo.get_contents(parent_folder, ref=output.branch)


def get_html(repo, output):
    """
    Fetches an output html file (an exported jupyter notebook) from a github repo based
    on `output`, an Output model instance.
    The notebook html consists of style, body and script tags.  Ignores any script tags.
    Return the style tags and html body content for display in template.
    """
    try:
        contents = repo.get_contents(output.output_html_file_path, ref=output.branch)
        last_updated = contents.last_modified
        contents = contents.decoded_content

    except GithubException:
        # If the single file was too big (>1Mb), we get an exception.  Get all the content
        # files from the parent folder instead (this doesn't download the actual content
        # itself, but gives us a list of ContentFile objects, from which we can obtain the
        # sha and retrieve the git blob instead
        parent_contents = get_parent_contents(repo, output)
        content_file = next(
            content_file
            for content_file in parent_contents
            if content_file.name == Path(output.output_html_file_path).name
        )
        last_updated = content_file.last_modified
        blob = repo.get_git_blob(content_file.sha)
        contents = b64decode(blob.content)
    last_updated_date = datetime.strptime(
        last_updated, "%a, %d %b %Y %H:%M:%S %Z"
    ).date()
    if output.last_updated != last_updated_date:
        output.last_updated = last_updated_date
        output.save()

    soup = BeautifulSoup(contents, "html.parser")
    style = soup.find_all("style")
    body = soup.find("body")
    style = [mark_safe(style_item.decode()) for style_item in style]
    contents = "".join(
        [
            content.decode() if isinstance(content, Tag) else content
            for content in body.contents
        ]
    )
    return {"body": mark_safe(contents), "style": style}
