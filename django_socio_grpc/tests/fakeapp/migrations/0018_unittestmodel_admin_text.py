# Generated by Django 5.1.6 on 2025-03-20 09:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fakeapp', '0017_enummodel_char_choices_no_default_no_null_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='unittestmodel',
            name='admin_text',
            field=models.CharField(max_length=100, null=True),
        ),
    ]
