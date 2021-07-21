from django.contrib import admin
from django.contrib.gis.db import models
from mapwidgets import GooglePointFieldWidget

from delivery.models import DeliveryInfo


class DeliveryInfoAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.PointField: {"widget": GooglePointFieldWidget}
    }
    raw_id_fields = ('transaction',)
    list_display = ('transaction', 'country', 'city', 'address', 'phone', 'delivery_organization')


admin.site.register(DeliveryInfo, DeliveryInfoAdmin)
