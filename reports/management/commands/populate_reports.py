import datetime
import os
import sys

from django.core.management.base import BaseCommand

from gateway.models import User
from reports.models import Category, Org, Report


class Command(BaseCommand):
    help = """
        Populate the database with sample reports if they are not already there.
        For development use only.
    """  # noqa: A003

    def handle(self, *args, **options):
        user = User.objects.first()
        if user is None:
            sys.exit("Please create a user before running this command")

        Category.objects.get_or_create(name="Archive")
        category, _ = Category.objects.get_or_create(name="Reports")

        bennett, _ = Org.objects.get_or_create(
            slug="bennett",
            defaults={
                "name": "Bennett Institute for Applied Data Science",
                "url": "https://bennett.ox.ac.uk",
            },
        )

        self.ensure_report(
            category,
            bennett,
            user,
            title="Vaccine Coverage",
            description="Weekly report on COVID-19 vaccination coverage in England",
            repo="output-explorer-test-repo",
            branch="master",
            report_html_file_path="test-outputs/vaccine-coverage-new.html",
        )

        if "INCLUDE_PRIVATE" in os.environ:  # pragma: no cover
            self.ensure_report(
                category,
                bennett,
                user,
                title="SRO Measures",
                description="Changes in key GP measures during the COVID-19 pandemic",
                repo="SRO-Measures",
                branch="master",
                report_html_file_path="released_outputs/output/sentinel_measures.html",
            )

            self.ensure_report(
                category,
                bennett,
                user,
                title="SRO Measures - Health Inequalities",
                description="Changes in key GP measures during the pandemic - health inequalities",
                repo="SRO-Measures",
                branch="master",
                report_html_file_path="released_outputs/output/sentinel_measures_demographics.html",
            )

    def ensure_report(self, category, org, user, **kwargs):
        report, created = get_or_create_with_validation(
            Report,
            category=category,
            org=org,
            publication_date=datetime.datetime(year=2021, month=5, day=10),
            created_by=user,
            updated_by=user,
            **kwargs,
        )
        if created:
            self.stderr.write(f"Created report '{report.title}'")
        else:
            # save existing reports to ensure repo links have been generated
            report.save()


# The built-in get_or_create() doesn't do validation, which we want here for safety and because it triggers the setup
# of derived fields as a side-effect. We follow the outline of the built-in version, but add a call to do the
# validation.
def get_or_create_with_validation(model, **params):
    try:
        return model.objects.get(**params), False
    except model.DoesNotExist:
        o = model(**params)
        o.full_clean()
        o.save()
        return o, True
