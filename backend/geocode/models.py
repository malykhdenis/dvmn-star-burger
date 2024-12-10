from django.utils import timezone
from django.db import models


class GeoCode(models.Model):
    address = models.CharField(
        'Адрес',
        max_length=200,
    )
    lon = models.FloatField('Долгота')
    lat = models.FloatField('Широта')
    created = models.DateTimeField('Время запроса', default=timezone.now)

    class Meta:
        unique_together = [['lon', 'lat'], ]

    def __str__(self) -> str:
        return f'Geo for {self.address}'
