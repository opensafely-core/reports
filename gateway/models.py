from pathlib import Path

import structlog
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django_extensions.db.fields import AutoSlugField
from github import GithubException, UnknownObjectException

from .github import get_parent_contents, get_repo


logger = structlog.getLogger()


class Organisation(models.Model):
    """An NHS Organisation"""

    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.code} - {self.name}"


class User(AbstractUser):
    organisations = models.ManyToManyField(Organisation)
    title = models.CharField(max_length=50, null=True, blank=True)
    display_name = models.CharField(max_length=255)

    def get_full_name(self):
        return self.display_name

    def save(self, *args, **kwargs):
        if not self.id:
            logger.info("User created", username=self.username)
        return super().save(*args, **kwargs)


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
        max_length=255, help_text="Path to the output html file within the repo"
    )
    slug = AutoSlugField(max_length=100, populate_from=["menu_name"], unique=True)

    def __str__(self):
        return self.slug

    def clean(self):
        """Validate the repo, branch and output file path on save"""
        try:
            repo = get_repo(self)
        except UnknownObjectException:
            raise ValidationError(f'Repo "{self.repo}" could not be found')

        try:
            parent_contents = get_parent_contents(repo, self)
        except GithubException as error:
            # This happens if either the branch or the output file's parent path is invalid
            raise ValidationError(
                f"Error fetching output file: {error.data['message']}"
            )

        if not any(
            content
            for content in parent_contents
            if content.name == Path(self.output_html_file_path).name
        ):
            raise ValidationError(
                f'File "{self.output_html_file_path}" could not be found (branch {self.branch})'
            )
        super().clean()
