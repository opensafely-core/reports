# Generated by Django 3.2.2 on 2021-06-01 08:32

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("reports", "0016_populate_menu_name_from_title"),
    ]

    operations = [
        migrations.AlterField(
            model_name="report",
            name="description",
            field=models.TextField(
                default="description",
                help_text="Short description to display before rendered report and in meta tags",
            ),
            preserve_default=False,
        ),
    ]
