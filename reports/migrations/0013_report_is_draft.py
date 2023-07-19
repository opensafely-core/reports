# Generated by Django 3.2.2 on 2021-05-26 09:52

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("reports", "0012_ordering_for_category_and_report"),
    ]

    operations = [
        migrations.AddField(
            model_name="report",
            name="is_draft",
            field=models.BooleanField(
                default=False,
                help_text="Draft reports are only visible by a logged in user with relevant permissions",
            ),
        ),
    ]
