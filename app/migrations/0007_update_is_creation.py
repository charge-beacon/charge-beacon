# Generated by Django 5.0.1 on 2024-01-14 19:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0006_alter_update_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='update',
            name='is_creation',
            field=models.BooleanField(default=False),
        ),
    ]
