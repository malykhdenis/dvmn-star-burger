# Generated by Django 3.2.15 on 2024-05-19 21:03

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0052_auto_20240512_1610'),
    ]

    operations = [
        migrations.RenameField(
            model_name='order',
            old_name='registrated_at',
            new_name='registered_at',
        ),
        migrations.AlterField(
            model_name='orderproduct',
            name='amount',
            field=models.SmallIntegerField(default=1, validators=[django.core.validators.MinValueValidator(1)], verbose_name='Количество'),
        ),
    ]
