from django.urls import path, include
from delivery import views
delivery_urls = [
    path('delivery/deliveryItemsCount/', views.DeliveryItemsCountView.as_view(), name='delivery_items_count'),
    path('delivery/ordersForDelivery/', views.DeliveryInfoListView.as_view(), name='delivery_orders'),

]
urlpatterns = [
    path('', include(delivery_urls)),
]
