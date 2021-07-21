from django.urls import path, include
from delivery import views
delivery_urls = [
    path('delivery/deliveryItemsCount/', views.DeliveryItemsCountView.as_view(), name='delivery_items_count'),

]
urlpatterns = [
    path('', include(delivery_urls)),
]
