# Generated by Django 5.1.6 on 2025-03-26 23:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0006_smartmeter_raw_client_secret'),
    ]

    operations = [
        migrations.AddField(
            model_name='smartmeter',
            name='last_ping_ts',
            field=models.DateTimeField(null=True),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='timestamp',
            field=models.DateTimeField(null=True),
        ),
    ]
