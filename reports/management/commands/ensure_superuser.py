from django.core.management.base import BaseCommand

from gateway.models import User


class Command(BaseCommand):
    help = """
        Create an admin/admin superuser if it doesn't already exist. For development use only.
    """  # noqa: A003

    def handle(self, *args, **options):
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@example.com", "admin")
