# Generated by Django 5.0.1 on 2024-01-18 19:41

import app.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0013_historicalstation_beacon_name_station_beacon_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicalstation',
            name='beacon_name',
            field=models.SlugField(default=app.models.get_beacon_name, max_length=255),
        ),
        migrations.AlterField(
            model_name='station',
            name='beacon_name',
            field=models.SlugField(default=app.models.get_beacon_name, max_length=255),
        ),
    ]
