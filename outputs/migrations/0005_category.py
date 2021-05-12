# Generated by Django 3.2.2 on 2021-05-12 14:17

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("outputs", "0004_output_use_git_blob"),
    ]

    operations = [
        migrations.CreateModel(
            name="Category",
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
                ("name", models.CharField(max_length=255, unique=True)),
            ],
        ),
        migrations.AddField(
            model_name="output",
            name="category",
            field=models.ForeignKey(
                help_text="Output category; used for navigation",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="outputs.category",
            ),
        ),
    ]
