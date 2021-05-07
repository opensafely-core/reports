# Generated by Django 3.2 on 2021-05-04 16:37

import django_extensions.db.fields
from django.db import migrations, models

import outputs.models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Output",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "menu_name",
                    models.CharField(
                        help_text="A short name to display in the side nav",
                        max_length=255,
                    ),
                ),
                (
                    "repo",
                    models.CharField(
                        help_text="Name of the OpenSAFELY repo (case insensitive)",
                        max_length=255,
                    ),
                ),
                ("branch", models.CharField(default="main", max_length=255)),
                (
                    "output_html_file_path",
                    models.CharField(
                        help_text="Path to the output html file within the repo",
                        max_length=255,
                        validators=[outputs.models.validate_html_filename],
                    ),
                ),
                (
                    "slug",
                    django_extensions.db.fields.AutoSlugField(
                        blank=True,
                        editable=False,
                        max_length=100,
                        populate_from=["menu_name"],
                        unique=True,
                    ),
                ),
            ],
        ),
    ]
