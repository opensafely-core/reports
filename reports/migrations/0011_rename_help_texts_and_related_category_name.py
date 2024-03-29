# Generated by Django 3.2.2 on 2021-05-25 10:34

import django.db.models.deletion
from django.db import migrations, models

import reports.models


class Migration(migrations.Migration):
    dependencies = [
        ("reports", "0010_rename_ouput_html_file_path_report_html_file_path"),
    ]

    operations = [
        migrations.AlterField(
            model_name="report",
            name="category",
            field=models.ForeignKey(
                help_text="Report category; used for navigation",
                on_delete=django.db.models.deletion.PROTECT,
                related_name="reports",
                to="reports.category",
            ),
        ),
        migrations.AlterField(
            model_name="report",
            name="description",
            field=models.TextField(
                blank=True,
                help_text="Optional description to display before rendered report",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="report",
            name="report_html_file_path",
            field=models.CharField(
                help_text="Path to the report html file within the repo",
                max_length=255,
                validators=[reports.models.validate_html_filename],
            ),
        ),
    ]
