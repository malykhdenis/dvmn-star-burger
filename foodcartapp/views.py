import logging

from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.templatetags.static import static
from environs import Env
from rest_framework.decorators import api_view
from rest_framework import serializers

from geocode.models import GeoCode

from .models import Order, OrderProduct, Product
from restaurateur.views import fetch_coordinates


env = Env()
env.read_env()

logging.basicConfig(
    format="%(process)d %(levelname)s %(message)s",
    level=logging.INFO
)


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            } if product.category else None,
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


class OrderProductSerializer(serializers.ModelSerializer):
    product = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(source='amount', min_value=1)

    class Meta:
        model = OrderProduct
        fields = ['product', 'quantity']

    def validate_product(self, value):
        if not Product.objects.filter(id=value).exists():
            raise serializers.ValidationError(
                f'product_id: нет продукта с id = {value}.'
            )
        return value


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


@api_view(['POST'])
def register_order(request):
    serializer = OrderSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return JsonResponse(serializer.data)
