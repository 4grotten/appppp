from django.contrib import admin
from django.contrib.gis.db import models
from mapwidgets import GooglePointFieldWidget

from delivery.models import DeliveryInfo


class DeliveryInfoAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.PointField: {"widget": GooglePointFieldWidget}
    }
    list_display = ('transaction', 'address', 'phone',)


admin.site.register(DeliveryInfo, DeliveryInfoAdmin)