# Generated by Django 4.1.1 on 2022-10-04 15:11

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("reports", "0027_add_report_is_external"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="report",
            name="is_external",
        ),
    ]
