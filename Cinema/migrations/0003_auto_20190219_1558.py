# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2019-02-19 07:58
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('Cinema', '0002_hall'),
    ]

    operations = [
        migrations.RenameField(
            model_name='hall',
            old_name='h_cinma',
            new_name='h_cinema',
        ),
    ]
