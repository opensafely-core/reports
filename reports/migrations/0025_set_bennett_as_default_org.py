# Generated by Django 4.1.1 on 2022-09-27 10:39

from django.db import migrations


def add_bennett_as_default_org(apps, schema_editor):
    Org = apps.get_model("reports", "Org")
    Report = apps.get_model("reports", "Report")

    bennett, _ = Org.objects.get_or_create(
        name="Bennett Institute of Applied Data Science", slug="bennett"
    )
    Report.objects.update(org=bennett)


def remove_bennett_org(apps, schema_editor):
    Org = apps.get_model("reports", "Org")
    Report = apps.get_model("reports", "Report")

    Report.objects.update(org=None)
    Org.objects.filter(slug="bennett").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("reports", "0024_add_org_model_and_link_to_reports"),
    ]

    operations = [
        migrations.RunPython(
            add_bennett_as_default_org,
            reverse_code=remove_bennett_org,
        )
    ]
