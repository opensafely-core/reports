import re
from pathlib import Path

import structlog
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_extensions.db.fields import AutoSlugField
from github import GithubException, UnknownObjectException

from .github import get_parent_contents, get_repo


logger = structlog.getLogger()


def validate_html_filename(value):
    if not re.match(r".*\.html?$", value):
        raise ValidationError(
            _("%(value)s must be an html file"),
            params={"value": value},
        )


class Output(models.Model):
    """
    An Output retrieved from an OpenSAFELY github repo
    Currently allows for single HTML output files only
    """

    menu_name = models.CharField(
        max_length=255, help_text="A short name to display in the side nav"
    )
    repo = models.CharField(
        max_length=255, help_text="Name of the OpenSAFELY repo (case insensitive)"
    )
    branch = models.CharField(max_length=255, default="main")
    output_html_file_path = models.CharField(
        max_length=255,
        help_text="Path to the output html file within the repo",
        validators=[validate_html_filename],
    )
    slug = AutoSlugField(max_length=100, populate_from=["menu_name"], unique=True)

    def __str__(self):
        return self.slug

    def clean(self):
        """Validate the repo, branch and output file path on save"""
        try:
            repo = get_repo(self)
        except UnknownObjectException:
            raise ValidationError(
                {"repo": _("'%(repo)s' could not be found") % {"repo": self.repo}}
            )

        try:
            parent_contents = get_parent_contents(repo, self)
        except GithubException as error:
            # This happens if either the branch or the output file's parent path is invalid
            raise ValidationError(
                _("Error fetching output file: %(error_message)s"),
                params={"error_message": error.data["message"]},
            )

        if not any(
            content
            for content in parent_contents
            if content.name == Path(self.output_html_file_path).name
        ):
            raise ValidationError(
                {
                    "output_html_file_path": _(
                        "File could not be found (branch %(branch)s)"
                    )
                    % {"branch": self.branch}
                }
            )
        super().clean()
