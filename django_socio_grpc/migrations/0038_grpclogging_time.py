# Generated by Django 2.2 on 2021-04-02 11:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_grpc_framework', '0037_grpclogging_message'),
    ]

    operations = [
        migrations.AddField(
            model_name='grpclogging',
            name='time',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]
