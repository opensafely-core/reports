# Generated by Django 4.0.3 on 2022-07-20 08:48

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("gateway", "0004_alter_user_organisations"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="user",
            name="organisations",
        ),
        migrations.DeleteModel(
            name="Organisation",
        ),
    ]
