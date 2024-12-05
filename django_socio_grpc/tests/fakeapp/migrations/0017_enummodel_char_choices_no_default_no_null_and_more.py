# Generated by Django 4.2.11 on 2024-12-05 10:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fakeapp', '0016_enummodel_char_choices_not_annotated'),
    ]

    operations = [
        migrations.AddField(
            model_name='enummodel',
            name='char_choices_no_default_no_null',
            field=models.CharField(choices=[('VALUE_1', 'Human readable value 1'), ('VALUE_2', 'Human readable value 2')], default='VALUE_1'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='enummodel',
            name='char_choices_nullable',
            field=models.CharField(blank=True, choices=[('VALUE_1', 'Human readable value 1'), ('VALUE_2', 'Human readable value 2')], null=True),
        ),
    ]