from django.urls import path, include
from delivery import views
delivery_urls = [
    path('delivery/deliveryItemsCount/', views.DeliveryItemsCountView.as_view(), name='delivery_items_count'),
    path('delivery/ordersForDelivery/', views.DeliveryInfoListView.as_view(), name='delivery_orders'),
    path('delivery/<int:pk>/acceptForDeliveryByCourier/', views.AcceptOrderForDeliveryByDeliveryService.as_view(), name='accept_for_delivery'),
    path('delivery/<int:pk>/rejectDeliveryByCourier/', views.RejectOrderForDeliveryByDeliveryService.as_view(), name='accept_for_delivery'),

]
urlpatterns = [
    path('', include(delivery_urls)),
]
