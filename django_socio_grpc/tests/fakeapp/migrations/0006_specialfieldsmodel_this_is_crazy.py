# Generated by Django 3.2 on 2021-05-03 15:11

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("fakeapp", "0005_specialfieldsmodel_list_datas"),
    ]

    operations = [
        migrations.AddField(
            model_name="specialfieldsmodel",
            name="this_is_crazy",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.JSONField(blank=True, default=dict),
                blank=True,
                default=list,
                size=None,
            ),
        ),
    ]
