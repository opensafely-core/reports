# Generated by Django 3.2.2 on 2021-05-12 16:03

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("reports", "0006_datamigration_add_default_category"),
    ]

    operations = [
        migrations.AlterField(
            model_name="output",
            name="category",
            field=models.ForeignKey(
                help_text="Output category; used for navigation",
                on_delete=django.db.models.deletion.CASCADE,
                to="reports.category",
            ),
        ),
    ]
