# Generated by Django 4.0.3 on 2022-04-13 12:00

from django.db import migrations, models

import reports.models


class Migration(migrations.Migration):

    dependencies = [
        ("reports", "0021_report_doi_verbose_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="report",
            name="job_server_url",
            field=models.URLField(blank=True, default="", max_length=255),
        ),
        migrations.AlterField(
            model_name="report",
            name="branch",
            field=models.CharField(blank=True, default="main", max_length=255),
        ),
        migrations.AlterField(
            model_name="report",
            name="repo",
            field=models.CharField(
                blank=True,
                help_text="Name of the OpenSAFELY repo (case insensitive)",
                max_length=255,
            ),
        ),
        migrations.AlterField(
            model_name="report",
            name="report_html_file_path",
            field=models.CharField(
                blank=True,
                help_text="Path to the report html file within the repo",
                max_length=255,
                validators=[reports.models.validate_html_filename],
            ),
        ),
    ]