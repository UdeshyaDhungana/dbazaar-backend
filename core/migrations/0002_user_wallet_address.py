# Generated by Django 3.2.8 on 2022-03-12 05:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='wallet_address',
            field=models.CharField(default='default', max_length=70),
            preserve_default=False,
        ),
    ]
