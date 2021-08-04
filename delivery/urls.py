from django.urls import path, include
from delivery import views
delivery_urls = [
    path('delivery/deliveryItemsCount/', views.DeliveryItemsCountView.as_view(), name='delivery_items_count'),
    path('delivery/ordersForDelivery/', views.DeliveryInfoListView.as_view(), name='delivery_orders'),
    path('delivery/<int:pk>/acceptForDeliveryByCourier/', views.AcceptOrderForDeliveryByDeliveryServiceView.as_view(), name='accept_for_delivery'),
    path('delivery/<int:pk>/rejectDeliveryByCourier/', views.RejectOrderForDeliveryByDeliveryServiceView.as_view(), name='reject_delivery'),
    path('delivery/<int:pk>/delivered/', views.DeliveredByDeliveryServiceView.as_view(), name='delivered'),
    path('delivery/history/', views.DeliveryServiceHistoryListView.as_view(), name='delivery_history'),
]
urlpatterns = [
    path('', include(delivery_urls)),
]
