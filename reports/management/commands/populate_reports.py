import datetime

from django.core.management.base import BaseCommand

from reports.models import Category, Report


class Command(BaseCommand):
    help = "Populate the database with sample reports if they are not already there. For development use only."

    def handle(self, *args, **options):
        category, _ = Category.objects.get_or_create(name="Reports")

        self.ensure_report(
            category,
            "Vaccine Coverage",
            "output-explorer-test-repo",
            "master",
            "test-outputs/vaccine-coverage-new.html",
        )

    def ensure_report(self, category, title, repo, branch, file_path):
        report, created = get_or_create_with_validation(
            Report,
            category=category,
            title=title,
            repo=repo,
            branch=branch,
            report_html_file_path=file_path,
            publication_date=datetime.datetime(year=2021, month=5, day=10),
        )
        if created:
            self.stderr.write(f"Created report '{report.title}'")


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
