from django.urls import path

from .views import ClientDiscountInfoView

urlpatterns = [
    path('transactions/preprocess/', ClientDiscountInfoView.as_view(), name='client-discounts'),
]
