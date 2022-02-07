# Generated by Django 3.2.8 on 2022-01-12 11:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0018_auto_20220112_1115'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='order',
            options={'permissions': [('cancel_order', 'Can cancel order')]},
        ),
        migrations.AlterField(
            model_name='customer',
            name='birthday',
            field=models.DateField(blank=True, null=True),
        ),
    ]