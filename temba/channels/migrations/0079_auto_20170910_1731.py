# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-09-10 17:31
from __future__ import unicode_literals

from django.db import migrations
import json


def populate_twilio_auth(apps, schema_editor):
    Channel = apps.get_model('channels', 'Channel')

    # copy our org level configs into our channel configs
    for channel in Channel.objects.filter(channel_type__in=['T', 'TMS'], is_active=True).select_related('org'):
        config = channel.config_json()
        config['account_sid'] = channel.org.config_json().get('ACCOUNT_SID')
        config['auth_token'] = channel.org.config_json().get('ACCOUNT_TOKEN')
        channel.config = json.dumps(config)
        channel.save(update_fields=['config'])

    # for consistency, remap twilio message service keys as well
    for channel in Channel.objects.filter(channel_type=['TW'], is_active=True):
        config = channel.config_json()
        config['account_sid'] = config.get('ACCOUNT_SID')
        config['auth_token'] = config.get('ACCOUNT_TOKEN')
        del config['ACCOUNT_SID']
        del config['ACCOUNT_TOKEN']
        channel.config = json.dumps(config)
        channel.save(update_fields=['config'])


class Migration(migrations.Migration):

    dependencies = [
        ('channels', '0078_auto_20170831_1830'),
    ]

    operations = [
        migrations.RunPython(populate_twilio_auth)
    ]
