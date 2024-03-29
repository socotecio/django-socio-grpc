# Generated by Django 4.1.4 on 2023-05-05 17:13

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('fakeapp', '0011_relatedfieldmodel_many_many_foreigns_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='RecursiveTestModel',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='fakeapp.recursivetestmodel')),
            ],
        ),
    ]
