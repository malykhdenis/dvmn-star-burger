import logging

import requests
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.templatetags.static import static
from phonenumber_field.phonenumber import PhoneNumber
from rest_framework.decorators import api_view
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


@api_view(['POST'])
def register_order(request):
    order_details = request.data

    if 'products' not in order_details:
        return Response({'error': 'products: Обязательное поле.'})
    elif not order_details['products'] and isinstance(order_details['products'], list):
        return Response({'error': 'products: Этот список не может быть пустым.'})
    elif not order_details['products']:
        return Response({'error': 'Поле products не может быть пустым.'})
    elif not isinstance(order_details['products'], list):
        return Response(
            {
                'error': f'Ожидался list со значениями, но был получен '
                         f'{type(order_details["products"])}.'
            }
        )
    if not ('firstname' in order_details or 'lastname' in order_details or 'phonenumber' in order_details or 'address' in order_details):
        return Response({'error': 'firstname, lastname, phonenumber, address: Обязательное поле.'})
    if not order_details['firstname'] and not order_details['lastname'] and not order_details['phonenumber'] and not order_details['address']:
        return Response({'error': 'firstname, lastname, phonenumber, address: Это поле не может быть пустым.'})
    if not isinstance(order_details['firstname'], str):
        return Response({'error': 'firstname: Not a valid string.'})
    if not order_details['phonenumber']:
        return Response({'error': 'phonenumber: Это поле не может быть пустым.'})
    if not order_details['firstname']:
        return Response({'error': 'firstname: Это поле не может быть пустым.'})

    number = PhoneNumber.from_string(order_details['phonenumber'])
    if not number.is_valid():
        return Response({'error': 'phonenumber: Введен некорректный номер телефона.'})

    for product_id in [product['product'] for product in order_details['products']]:
        try:
            product = get_object_or_404(Product, id=product_id)
        except Exception:
            return Response({'error': f'products: Недопустимый первичный ключ {product_id}'})

    order, created = Order.objects.get_or_create(
        phone_number=order_details['phonenumber'],
        defaults={
            'first_name': order_details['firstname'],
            'last_name': order_details['lastname'],
            'address': order_details['address']
        }
    )
    if created:
        logging.info(f'Order {order.id} is created')
        products = order_details['products']
        for product in products:
            product_in_order, created = OrderProduct.objects.get_or_create(
                product=get_object_or_404(Product, id=product['product']),
                order=Order.objects.get(id=order.id),
                amount=product['quantity'],
            )
            if created:
                logging.info(
                    f'{product_in_order.product.name} added to order '
                    f'{product_in_order.order.id}'
                )
    return JsonResponse({})
