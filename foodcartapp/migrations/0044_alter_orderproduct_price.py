# Generated by Django 3.2.15 on 2024-05-04 23:25

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0043_set_orderpoduct_price'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderproduct',
            name='price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True, validators=[django.core.validators.MinValueValidator(0)], verbose_name='цена'),
        ),
    ]
