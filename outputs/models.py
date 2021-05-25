import re
from uuid import uuid4

import structlog
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_extensions.db.fields import AutoSlugField

from .github import GithubAPIException, GitHubOutput


logger = structlog.getLogger()


def validate_html_filename(value):
    if not re.match(r".*\.html?$", value):
        raise ValidationError(
            _("%(value)s must be an html file"),
            params={"value": value},
        )


class PopulatedCategoryManager(models.Manager):
    """
    Manager that returns only Categories that have at least one associated Output
    """

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .annotate(count=models.Count("outputs"))
            .filter(count__gt=0)
        )


class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    objects = models.Manager()
    populated = PopulatedCategoryManager()

    class Meta:
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Report(models.Model):
    """
    A report retrieved from an OpenSAFELY github repo
    Currently allows for single HTML output files only
    """

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        help_text="Output category; used for navigation",
        related_name="outputs",
    )
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

    # front matter fields
    authors = models.TextField(null=True, blank=True)
    title = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(
        null=True,
        blank=True,
        help_text="Optional description to display before rendered output",
    )
    publication_date = models.DateField(help_text="Date published")
    last_updated = models.DateField(
        null=True,
        blank=True,
        help_text="File last modified date; autopopulated from GitHub",
    )
    cache_token = models.UUIDField(default=uuid4)
    # Flag to remember if this output needed to use the git blob method (see github.py),
    # to avoid re-calling the contents endpoint if we know it will fail
    use_git_blob = models.BooleanField(default=False)

    def __str__(self):
        return self.slug

    def refresh_cache_token(self):
        self.cache_token = uuid4()
        self.save()

    def clean(self):
        """Validate the repo, branch and output file path on save"""
        # Disable caching to fetch the repo and contents.  If this is a new output file in
        # an existing folder, we don't want to use a previously cached request
        github_output = GitHubOutput(self, use_cache=False)
        try:
            github_output.repo
        except GithubAPIException:
            raise ValidationError(
                {"repo": _("'%(repo)s' could not be found") % {"repo": self.repo}}
            )

        try:
            github_output.get_parent_contents()
        except GithubAPIException as error:
            # This happens if either the branch or the output file's parent path is invalid
            raise ValidationError(
                _("Error fetching report file: %(error_message)s"),
                params={"error_message": str(error)},
            )

        if not any(github_output.matching_output_file_from_parent_contents()):
            raise ValidationError(
                {
                    "output_html_file_path": _(
                        "File could not be found (branch %(branch)s)"
                    )
                    % {"branch": self.branch}
                }
            )
        super().clean()

    def get_absolute_url(self):
        return reverse("outputs:report_view", args=(self.slug, self.cache_token))
