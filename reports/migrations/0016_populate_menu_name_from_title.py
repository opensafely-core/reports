# Generated by Django 3.2.2 on 2021-05-28 12:56

import django_extensions.db.fields
from django.db import migrations, models
from django.db.models import F

import reports.models


def populate_title_from_menu_name(apps, _):
    apps.get_model("reports", "Report").objects.filter(title=None).update(
        title=F("menu_name")
    )


class Migration(migrations.Migration):
    dependencies = [
        ("reports", "0015_report_contact_email"),
    ]

    operations = [
        migrations.RunPython(
            code=populate_title_from_menu_name,
            # There's no reasonable way to reverse this, but having the title populated is harmless.
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="report",
            name="menu_name",
            field=reports.models.AutoPopulatingCharField(
                help_text="A short name to display in the side nav",
                max_length=60,
                populate_from="title",
            ),
        ),
        migrations.AlterField(
            model_name="report",
            name="slug",
            field=django_extensions.db.fields.AutoSlugField(
                blank=True,
                editable=False,
                max_length=100,
                populate_from=["title"],
                unique=True,
            ),
        ),
        migrations.AlterField(
            model_name="report",
            name="title",
            field=models.CharField(default="don't check this in", max_length=255),
            preserve_default=False,
        ),
    ]
