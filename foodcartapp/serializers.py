import logging

from django.db import transaction
from django.shortcuts import get_object_or_404
from environs import Env
from rest_framework import serializers

from foodcartapp.models import Order, OrderProduct, Product
from geocode.models import GeoCode
from restaurateur.views import fetch_coordinates


env = Env()
env.read_env()


class OrderProductSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(read_only=True)
    quantity = serializers.IntegerField(source='amount', min_value=1)

    class Meta:
        model = OrderProduct
        fields = ['product', 'quantity']


class OrderSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    products = OrderProductSerializer(
        many=True,
        allow_empty=False,
        write_only=True
    )

    class Meta:
        model = Order
        fields = '__all__'

    @transaction.atomic
    def create(self, validated_data):
        order, created = Order.objects.get_or_create(
            phonenumber=validated_data['phonenumber'],
            defaults={
                'firstname': validated_data['firstname'],
                'lastname': validated_data['lastname'],
                'address': validated_data['address']
            }
        )
        if created:
            logging.info(f'Order {order.id} is created')
            products = validated_data['products']
            for product_details in products:
                product = get_object_or_404(
                    Product, id=product_details['product']
                )
                product_in_order, created = OrderProduct.objects.get_or_create(
                    product=product,
                    order=order,
                    amount=product_details['amount'],
                    price=product_details.get('price', product.price)
                )
                if created:
                    logging.info(
                        f'{product_in_order.product.name} added to order '
                        f'{product_in_order.order.id}'
                    )

        order_lon, order_lat = fetch_coordinates(
            env.str('YANDEX_API_KEY'),
            order.address,
        )
        geo, created = GeoCode.objects.get_or_create(
            address=order.address,
            lon=order_lon,
            lat=order_lat,
        )
        if created:
            logging.info(f'Geo for order {order.id} created.')

        order.geo = geo
        order.save()

        return order
