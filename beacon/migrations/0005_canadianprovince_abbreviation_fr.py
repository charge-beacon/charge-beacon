# Generated by Django 5.0.1 on 2024-01-22 19:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('beacon', '0004_alter_zipcodetabulationarea_area_canadianprovince_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='canadianprovince',
            name='abbreviation_fr',
            field=models.CharField(default='', max_length=10),
            preserve_default=False,
        ),
    ]
