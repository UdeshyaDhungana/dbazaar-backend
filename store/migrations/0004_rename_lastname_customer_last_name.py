# Generated by Django 3.2.8 on 2021-10-30 04:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0003_rename_firstname_customer_first_name'),
    ]

    operations = [
        migrations.RenameField(
            model_name='customer',
            old_name='lastname',
            new_name='last_name',
        ),
    ]
