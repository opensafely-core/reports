from django.core.management.base import BaseCommand

from reports.groups import setup_researchers


class Command(BaseCommand):
    help = (  # noqa: A003
        "Ensure the researchers group exists with relevant permissions."
    )

    def handle(self, *args, **options):
        setup_researchers()
