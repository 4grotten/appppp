from django.urls import path, include

delivery_urls = [
    path('deliveryItemsCount/', DeliveryItemsCountView.as_view(), name='delivery_items_count'),

]
urlpatterns = [
    path('', include(delivery_urls)),
]
