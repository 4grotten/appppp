from django.urls import path

from stock.views import FormatCriteriaListView, SizeByFormatListView, CriteriaSubcategoryListView, CreateStokeCartView, \
    SizeQuantityListCreateView, CreateShopItemCollections, AvailableSizeListView, RemoveShopItemStock, \
    RemoveShopItemSizeQuantity, CreateShopItemLinkCollections

urlpatterns = [
    path('criteria_by_subcategory/<int:pk>/', CriteriaSubcategoryListView.as_view(), name='criteria_by_subcategory'),
    path('format_by_criteria/<int:pk>/', FormatCriteriaListView.as_view(), name='format_by_criteria'),
    path('size_by_format/<int:pk>/', SizeByFormatListView.as_view(), name='size_by_format'),
    path('stock_cart/<int:pk>/', CreateStokeCartView.as_view(), name='stock_cart_create'),
    path('size_quantity/<int:pk>/', SizeQuantityListCreateView.as_view(), name='add_size_count'),
    path('shop_item_collection/<int:pk>/', CreateShopItemCollections.as_view(), name='create_shop_item_collection'),
    path('shop_item_link_collection/<int:pk>/', CreateShopItemLinkCollections.as_view(), name='create_shop_item_link_collection'),
    path('available_size_in_stock_cart/<int:pk>/', AvailableSizeListView.as_view(), name='available_size_in_stock_cart'),

    path('remove_shop_item_cart/<int:pk>/', RemoveShopItemStock.as_view(), name='remove_shop_item_cart'),
    path('remove_shop_item_size_quantity/<int:pk>/', RemoveShopItemSizeQuantity.as_view(), name='remove_shop_item_size_quantity'),
]
