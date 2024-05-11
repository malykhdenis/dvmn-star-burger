from django.db import models
from django.db.models import F, Sum
from django.core.validators import MinValueValidator
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField


class Restaurant(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
            .filter(availability=True)
            .values_list('product')
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        'картинка'
    )
    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'описание',
        max_length=200,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class OrderQuerySet(models.QuerySet):
    def in_process(self):
        return self.exclude(status='4_ready')

    def add_total_price(self):
        return self.annotate(
            total_price=Sum(
                F('products_inside__price') * F('products_inside__amount')
            )
        )


class Order(models.Model):
    ORDER_STATUS = [
        ('1_manager', 'Обработка заказа'),
        ('2_cooking', 'Приготовление заказа'),
        ('3_delivery', 'Доставка заказа'),
        ('4_ready', 'Готово'),
    ]
    PAYMENT = [
        ('online', 'Онлайн на сайте'),
        ('card', 'Картой курьеру'),
        ('cash', 'Наличными курьеру'),
    ]
    firstname = models.CharField('Имя', max_length=50)
    lastname = models.CharField('Фамилия', max_length=50, blank=True)
    phonenumber = PhoneNumberField(region='RU')
    address = models.CharField('Адрес', max_length=200, blank=True)
    products = models.ManyToManyField(
        Product,
        through='OrderProduct',
        db_index=True,
    )
    status = models.CharField(
        'Статус заказа',
        max_length=100,
        choices=ORDER_STATUS,
        db_index=True,
    )
    comment = models.TextField(
        'Комментарий',
        blank=True,
        help_text='Комментарий к заказу',
    )
    registrated_at = models.DateTimeField(
        'Зарегестрирован',
        default=timezone.now,
        db_index=True)
    called_at = models.DateTimeField(
        'Время звонка',
        blank=True,
        null=True,
    )
    delivered_at = models.DateTimeField(
        'Время доставки',
        blank=True,
        null=True,
    )
    payment = models.CharField(
        'Способ оплаты',
        max_length=100,
        choices=PAYMENT,
        db_index=True,
    )
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='order',
        verbose_name='Где будет готовиться',
        blank=True,
        null=True,
    )

    objects = OrderQuerySet.as_manager()

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self):
        return f"Заказ {self.id}"


class OrderProduct(models.Model):
    order = models.ForeignKey(
        Order,
        related_name='products_inside',
        on_delete=models.CASCADE,
        db_index=True,
    )
    product = models.ForeignKey(
        Product,
        related_name='orders',
        on_delete=models.CASCADE,
        db_index=True,
    )
    amount = models.SmallIntegerField(
        'Количество',
        default=1,
        validators=[MinValueValidator(0),],
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = 'Продукты в заказе'
        verbose_name_plural = 'Продукты в заказах'
        unique_together = [
            ['order', 'product']
        ]

    def __str__(self):
        return f"{self.product} в заказе {self.order.id}"
