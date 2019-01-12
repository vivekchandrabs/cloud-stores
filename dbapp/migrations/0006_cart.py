# Generated by Django 2.1.1 on 2018-10-16 12:30

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dbapp', '0005_auto_20181002_1535'),
    ]

    operations = [
        migrations.CreateModel(
            name='Cart',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('shopkeeper', models.CharField(blank=True, max_length=100)),
                ('items', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(blank=True, max_length=100), size=500)),
            ],
        ),
    ]