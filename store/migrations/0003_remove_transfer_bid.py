# Generated by Django 3.2.8 on 2022-03-08 04:45

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0002_transfer_bid'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='transfer',
            name='bid',
        ),
    ]
