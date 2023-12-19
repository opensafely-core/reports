# Generated by Django 4.2.7 on 2023-12-19 14:57
from django.db import migrations
from django.db.models import F, Q


def add_trailing_slashes_to_jobserver_urls_missing_them(apps, schema_editor):
    Report = apps.get_model("reports", "Report")

    Report.objects.exclude(
        Q(job_server_url="") | Q(job_server_url__endswith="/")
    ).update(job_server_url=F("job_server_url") + "/")


class Migration(migrations.Migration):
    dependencies = [
        ("reports", "0034_default_is_draft_to_true"),
    ]

    operations = [
        migrations.RunPython(
            add_trailing_slashes_to_jobserver_urls_missing_them,
            reverse_code=migrations.RunPython.noop,
        )
    ]
