from django.contrib import admin

from .models import GeoCode


@admin.register(GeoCode)
class RestaurantAdmin(admin.ModelAdmin):
    pass
