# Generated by Django 5.0.9 on 2024-11-12 11:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("fakeapp", "0015_enummodel_int_choices_alter_enummodel_char_choices"),
    ]

    operations = [
        migrations.AddField(
            model_name="enummodel",
            name="char_choices_not_annotated",
            field=models.CharField(
                choices=[
                    ("VALUE_1", "Human readable value 1"),
                    ("VALUE_2", "Human readable value 2"),
                ],
                default="VALUE_1",
            ),
        ),
    ]
