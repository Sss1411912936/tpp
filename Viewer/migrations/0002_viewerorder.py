# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2019-02-21 03:53
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Cinema', '0004_paidang'),
        ('Viewer', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ViewerOrder',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('v_expire', models.DateTimeField(default=datetime.datetime(2019, 2, 21, 12, 8, 27, 653496))),
                ('v_price', models.FloatField(default=1)),
                ('v_status', models.IntegerField(default=0)),
                ('v_seats', models.CharField(max_length=256)),
                ('v_paidang', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Cinema.PaiDang')),
                ('v_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Viewer.ViewerUser')),
            ],
        ),
    ]
