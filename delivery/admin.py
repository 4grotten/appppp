from django.contrib import admin
from django.contrib.gis.db import models
from mapwidgets import GooglePointFieldWidget

from delivery.models import DeliveryInfo, DeliveryActionHistory


class DeliveryInfoAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.PointField: {"widget": GooglePointFieldWidget}
    }
    raw_id_fields = ('transaction', 'delivery_organization', 'city')
    list_display = ('transaction', 'country', 'city', 'address', 'phone', 'delivery_organization', 'status', 'who_pays')
    list_filter = ('status', 'who_pays')

class DeliveryActionHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'delivery_info','delivery_organization', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    raw_id_fields = ('delivery_info', 'delivery_organization')

admin.site.register(DeliveryInfo, DeliveryInfoAdmin)
admin.site.register(DeliveryActionHistory, DeliveryActionHistoryAdmin)
