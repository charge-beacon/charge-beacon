# Generated by Django 5.0.1 on 2024-01-14 20:01

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0009_alter_station_linked'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='station',
            name='linked',
        ),
        migrations.AddField(
            model_name='historicalstation',
            name='linked_to',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='app.station'),
        ),
        migrations.AddField(
            model_name='station',
            name='linked_to',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='linked', to='app.station'),
        ),
    ]
