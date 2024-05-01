import logging

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.templatetags.static import static
from rest_framework.decorators import api_view
from rest_framework import serializers
from rest_framework.response import Response

from .models import Order, OrderProduct, Product


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
    products = OrderProductSerializer(many=True, allow_empty=False)

    class Meta:
        model = Order
        fields = '__all__'


@api_view(['POST'])
def register_order(request):
    order = serializer = OrderSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    order, created = Order.objects.get_or_create(
        phonenumber=serializer.validated_data['phonenumber'],
        defaults={
            'firstname': serializer.validated_data['firstname'],
            'lastname': serializer.validated_data['lastname'],
            'address': serializer.validated_data['address']
        }
    )
    if created:
        logging.info(f'Order {order.id} is created')
        products = serializer.validated_data['products']
        for product in products:
            product_in_order, created = OrderProduct.objects.get_or_create(
                product=get_object_or_404(Product, id=product['product']),
                order=order,
                amount=product['amount'],
            )
            if created:
                logging.info(
                    f'{product_in_order.product.name} added to order '
                    f'{product_in_order.order.id}'
                )
    return Response({'order_id': order.id, })
