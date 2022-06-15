from django.urls import path

from stock.views import FormatSizeListView, ShopItemSizeByFormatView

urlpatterns = [
    path('format_sizes/', FormatSizeListView.as_view(), name='format_sizes'),
    path('shop_item_sizes/<int:pk>/', ShopItemSizeByFormatView.as_view(), name='shop_item_sizes'),
]
