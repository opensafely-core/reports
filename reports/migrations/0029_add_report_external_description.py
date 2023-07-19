# Generated by Django 4.1.1 on 2022-10-04 14:02

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("reports", "0028_remove_report_is_external"),
    ]

    operations = [
        migrations.AddField(
            model_name="report",
            name="external_description",
            field=models.TextField(
                blank=True,
                default="",
                help_text="A description of why this report, from an external organisation, is on the OpenSAFELY Reports website.",
            ),
        ),
    ]
