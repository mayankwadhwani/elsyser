# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2017-08-04 09:15
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('exams', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='exam',
            name='topic',
            field=models.CharField(max_length=60),
        ),
    ]