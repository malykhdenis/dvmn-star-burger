# Generated by Django 3.2.15 on 2024-05-05 17:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0044_alter_orderproduct_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('manager', 'Обработка заказа'), ('coocking', 'Приготовление заказа'), ('delivery', 'Доставка заказа'), ('ready', 'Готово')], default='manager', max_length=100, verbose_name='Статус заказа'),
            preserve_default=False,
        ),
    ]
