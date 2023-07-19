# Generated by Django 3.2.2 on 2021-05-27 16:06

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("reports", "0014_report_view_draft_permission"),
    ]

    operations = [
        migrations.AddField(
            model_name="report",
            name="contact_email",
            field=models.EmailField(default="team@opensafely.org", max_length=254),
        ),
    ]
