# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-04-25 12:19
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0002_auto_20170424_2108'),
    ]

    operations = [
        migrations.AddField(
            model_name='conversation',
            name='current_message',
            field=models.TextField(default=''),
        ),
        migrations.AddField(
            model_name='conversation',
            name='previous_message',
            field=models.TextField(default=''),
        ),
    ]
