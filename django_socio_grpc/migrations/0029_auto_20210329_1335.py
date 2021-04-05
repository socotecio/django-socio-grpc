# Generated by Django 2.2 on 2021-03-29 11:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('django_grpc_framework', '0028_grpcmethod_input'),
    ]

    operations = [
        migrations.AddField(
            model_name='grcpprotobuffields',
            name='is_update',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='grpcmethod',
            name='database',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='django_grpc_framework.grcpDataBases', verbose_name='Database'),
        ),
        migrations.AlterField(
            model_name='grpcmethod',
            name='is_update',
            field=models.BooleanField(default=False, verbose_name='Updade'),
        ),
        migrations.AlterField(
            model_name='grpcmethod',
            name='service',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='django_grpc_framework.grcpMicroServices', verbose_name='Microservice'),
        ),
    ]
