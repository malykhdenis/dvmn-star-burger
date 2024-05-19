import logging

import requests
from django import forms
from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views
from environs import Env
from geopy import distance

from foodcartapp.models import Order, Product, Restaurant
from geocode.models import GeoCode


env = Env()
env.read_env()

logging.basicConfig(
    format="%(process)d %(levelname)s %(message)s",
    level=logging.INFO
)


class Login(forms.Form):
    username = forms.CharField(
        label='Логин', max_length=75, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Укажите имя пользователя'
        })
    )
    password = forms.CharField(
        label='Пароль', max_length=75, required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(request, "login.html", context={
            'form': form
        })

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:  # FIXME replace with specific permission
                    return redirect("restaurateur:RestaurantView")
                return redirect("start_page")

        return render(request, "login.html", context={
            'form': form,
            'ivalid': True,
        })


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('restaurateur:login')


def is_manager(user):
    return user.is_staff  # FIXME replace with specific permission


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_products(request):
    restaurants = list(Restaurant.objects.order_by('name'))
    products = list(Product.objects.prefetch_related('menu_items'))

    products_with_restaurant_availability = []
    for product in products:
        availability = {
            item.restaurant_id: item.availability
            for item
            in product.menu_items.all()
        }
        ordered_availability = [
            availability.get(restaurant.id, False)
            for restaurant
            in restaurants
        ]

        products_with_restaurant_availability.append(
            (product, ordered_availability)
        )

    return render(
        request,
        template_name="products_list.html",
        context={
            'products_with_restaurant_availability':
                products_with_restaurant_availability,
            'restaurants': restaurants,
        }
    )


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_restaurants(request):
    return render(request, template_name="restaurants_list.html", context={
        'restaurants': Restaurant.objects.all(),
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    orders = Order.objects.in_process().add_total_price().order_by('status')
    order_restaurants = list()

    for order in orders:
        available_restaurants = set()
        products = [
            order_product.product
            for order_product
            in order.products_inside.all()
        ]
        for product in products:
            product_restaurants = [
                item.restaurant
                for item
                in product.menu_items.filter(availability=True)
            ]
        if not available_restaurants:
            available_restaurants = set(product_restaurants)
        else:
            available_restaurants = available_restaurants & set(
                product_restaurants
            )

        restaurants_with_distance = list()
        if not order.geo or not GeoCode.objects.filter(address=order.address):
            create_geo(order)
        for restaurant in available_restaurants:
            if not restaurant.geo:
                create_geo(restaurant)
            try:
                distance = str(round(
                    get_distance(
                        (order.geo.lon, order.geo.lat),
                        (restaurant.geo.lon, restaurant.geo.lat),
                    ),
                    3,
                )) + 'км'
            except Exception:
                distance = 'Ошибка определения координат'
            restaurants_with_distance.append((restaurant, distance))

        restaurants_with_distance.sort(key=lambda item: item[1])

    order_restaurants.append((order, restaurants_with_distance))

    return render(
        request,
        template_name='order_items.html',
        context={
            'order_items': order_restaurants,
        }
    )


def fetch_coordinates(apikey, address):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(base_url, params={
        "geocode": address,
        "apikey": apikey,
        "format": "json",
    })
    response.raise_for_status()
    found_places = response.json()['response']['GeoObjectCollection'][
        'featureMember']

    if not found_places:
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return lon, lat


def get_distance(client_coordinates, restaurant_coordinates):
    if not client_coordinates or not restaurant_coordinates:
        raise Exception('Ошибка определения координат')
    return distance.distance(client_coordinates, restaurant_coordinates).km


def create_geo(place):
    """Create GeoCode object for place."""
    lon, lat = fetch_coordinates(
        env.str('YANDEX_API_KEY'),
        place.address,
    )
    if lat and lon:
        geo, created = GeoCode.objects.get_or_create(
            address=place.address,
            lon=lon,
            lat=lat,
        )
        if created:
            logging.info(f'Geo for order {place.address} created.')
            place.geo = geo
            place.save()
