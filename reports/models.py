import re
from uuid import uuid4

import structlog
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_extensions.db.fields import AutoSlugField

from .github import GithubAPIException, GithubReport


logger = structlog.getLogger()


def validate_html_filename(value):
    if not re.match(r".*\.html?$", value):
        raise ValidationError(
            _("%(value)s must be an html file"),
            params={"value": value},
        )


class PopulatedCategoryManager(models.Manager):
    """
    Manager that returns only Categories that have at least one associated Report
    """

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .annotate(count=models.Count("reports"))
            .filter(count__gt=0)
        ).order_by("name")

    def for_user(self, user):
        report_category_ids = set(
            Report.objects.for_user(user).values_list("category_id", flat=True)
        )
        return self.get_queryset().filter(id__in=report_category_ids).order_by("name")


class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    objects = models.Manager()
    populated = PopulatedCategoryManager()

    class Meta:
        verbose_name_plural = "categories"
        ordering = ("name",)

    def __str__(self):
        return self.name


class ReportManager(models.Manager):
    """
    Manager that can returns only Reports that a particular user has access to
    """

    def for_user(self, user):
        queryset = self.get_queryset()
        if user.has_perm("reports.view_draft"):
            return queryset
        return queryset.filter(is_draft=False)


class Report(models.Model):
    """
    A report retrieved from an OpenSAFELY github repo
    Currently allows for single HTML report files only
    """

    objects = ReportManager()
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        help_text="Report category; used for navigation",
        related_name="reports",
    )
    menu_name = models.CharField(
        max_length=255, help_text="A short name to display in the side nav"
    )
    repo = models.CharField(
        max_length=255, help_text="Name of the OpenSAFELY repo (case insensitive)"
    )
    branch = models.CharField(max_length=255, default="main")
    report_html_file_path = models.CharField(
        max_length=255,
        help_text="Path to the report html file within the repo",
        validators=[validate_html_filename],
    )
    slug = AutoSlugField(max_length=100, populate_from=["menu_name"], unique=True)

    # front matter fields
    authors = models.TextField(null=True, blank=True)
    title = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(
        null=True,
        blank=True,
        help_text="Optional description to display before rendered report",
    )
    publication_date = models.DateField(help_text="Date published")
    last_updated = models.DateField(
        null=True,
        blank=True,
        help_text="File last modified date; autopopulated from GitHub",
    )
    cache_token = models.UUIDField(default=uuid4)
    # Flag to remember if this report needed to use the git blob method (see github.py),
    # to avoid re-calling the contents endpoint if we know it will fail
    use_git_blob = models.BooleanField(default=False)
    is_draft = models.BooleanField(
        default=False,
        help_text="Draft reports are only visible by a logged in user with relevant permissions",
    )

    contact_email = models.EmailField(default="team@opensafely.org")

    class Meta:
        ordering = ("menu_name",)
        permissions = [
            ("view_draft", "Can view draft reports"),
        ]

    def __str__(self):
        return self.slug

    def refresh_cache_token(self):
        self.cache_token = uuid4()
        self.save()

    def clean(self):
        """Validate the repo, branch and report file path on save"""
        # Disable caching to fetch the repo and contents.  If this is a new report file in
        # an existing folder, we don't want to use a previously cached request
        github_report = GithubReport(self, use_cache=False)
        try:
            github_report.repo
        except GithubAPIException:
            raise ValidationError(
                {"repo": _("'%(repo)s' could not be found") % {"repo": self.repo}}
            )

        try:
            github_report.get_parent_contents()
        except GithubAPIException as error:
            # This happens if either the branch or the report file's parent path is invalid
            raise ValidationError(
                _("Error fetching report file: %(error_message)s"),
                params={"error_message": str(error)},
            )

        if not any(github_report.matching_report_file_from_parent_contents()):
            raise ValidationError(
                {
                    "report_html_file_path": _(
                        "File could not be found (branch %(branch)s)"
                    )
                    % {"branch": self.branch}
                }
            )
        super().clean()

    def get_absolute_url(self):
        return reverse("reports:report_view", args=(self.slug, self.cache_token))
