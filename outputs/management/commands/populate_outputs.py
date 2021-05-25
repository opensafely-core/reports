import datetime

from django.core.management.base import BaseCommand

from outputs.models import Category, Report


class Command(BaseCommand):
    help = "Populate the database with sample reports if they are not already there. For development use only."

    def handle(self, *args, **options):
        category, _ = Category.objects.get_or_create(name="Reports")
        output, created = Report.objects.get_or_create(
            category=category,
            menu_name="Vaccine Coverage",
            repo="nhs-covid-vaccination-coverage",
            branch="master",
            output_html_file_path="released-outputs/opensafely_vaccine_report_overall.html",
            title="Vaccine Coverage",
            publication_date=datetime.datetime(year=2021, month=5, day=10),
        )

        if created:
            self.stderr.write(f"Created report '{output.title}'")
