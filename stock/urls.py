from django.urls import path

# from stock.views import FormatCriteriaListView, SizeByFormatListView, CriteriaSubcategoryListView, \
    # GetOrCreateStockCollection, FillStockCollectionBySiza
from stock.views import FormatCriteriaListView, SizeByFormatListView, CriteriaSubcategoryListView, \
    DownloadOrgDeliveryInfoAPIView, AvailableSizeListCreateView, ShopItemsSetCreateView, GetShopItemByLink, \
    ShopItemSetListView, ShopItemLinkSetListView, ShopItemSizeCountView, GetNotChoosenSizeListView, DeleteStockView, \
    DeleteShopItemSizeCountView, StockView

urlpatterns = [
    path('criteria_by_subcategory/<int:pk>/', CriteriaSubcategoryListView.as_view(), name='criteria_by_subcategory'),
    path('format_by_criteria/<int:pk>/', FormatCriteriaListView.as_view(), name='format_by_criteria'),
    path('size_by_format/<int:pk>/', SizeByFormatListView.as_view(), name='size_by_format'),

    path('available_sizes/shop_items/<int:pk>/', AvailableSizeListCreateView.as_view(), name='available_sizes'),
    path('add_shop_items_set/<int:pk>/', ShopItemsSetCreateView.as_view(), name='shop_items_set'),
    path('get_shop_item_by_link/', GetShopItemByLink.as_view(), name='get_shop_item_by_link'),
    path('get_shop_item_set/<int:pk>/', ShopItemSetListView.as_view(), name='get_shop_item_by_link'),
    path('get_shop_item_link_set/<int:pk>/', ShopItemLinkSetListView.as_view(), name='get_shop_item_by_link'),
    path('shop_item_size_count/<int:pk>/', ShopItemSizeCountView.as_view(), name='get_shop_item_size_count'),
    path('get_not_choosen_sizes/<int:pk>/', GetNotChoosenSizeListView.as_view(), name='get_not_choosen_sizes'),
    path('delete_stock/<int:pk>/', DeleteStockView.as_view(), name='delete_stock'),
    path('delete_shop_item_size/<int:pk>/', DeleteShopItemSizeCountView.as_view(), name='delete_shop_item_size'),


    path('get_stock/<int:pk>/', StockView.as_view(), name='get_stock'),

    # path('stock/collection/shop_item/<int:pk>/', GetOrCreateStockCollection.as_view(), name='stock_collection'),
    # path('stock/shop_item/<int:shop_item_id>/criteria/<int:criteria_id>/', FillStockCollectionBySiza.as_view(),
    #      name='stock_collection'),
    # path('stock_cart/<int:pk>/', CreateStokeCartView.as_view(), name='stock_cart_create'),
    # path('size_quantity/<int:pk>/', SizeQuantityListCreateView.as_view(), name='add_size_count'),
    # path('shop_item_collection/<int:pk>/', CreateShopItemCollections.as_view(), name='create_shop_item_collection'),
    # path('shop_item_link_collection/<int:pk>/', CreateShopItemLinkCollections.as_view(), name='create_shop_item_link_collection'),
    path('download_org_delivery_info/<int:pk>/', DownloadOrgDeliveryInfoAPIView.as_view(),
         name='download_organization_delivery_info'),
]
