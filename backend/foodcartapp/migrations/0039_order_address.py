# Generated by Django 3.2.15 on 2024-04-29 21:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0038_auto_20240429_2307'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='address',
            field=models.CharField(blank=True, max_length=200, verbose_name='Адрес'),
        ),
    ]