from django.urls import path

from shop.views.cart_views import CartItemCountChangeView, UserCartListView, UserCartRetrieveDestroyView, OrderDeliveryView
from shop.views.category_views import (
    ItemCategoriesListView, ItemCategoryRetrieveUpdateDestroyView, ItemCategoriesCreateView,
    OrganizationSubcategoriesView
)
from shop.views.feed_views import FeedView, OrganizationItemListView
from shop.views.item_views import (
    ItemCreateView, ItemRetrieveUpdateDestroyView, ItemChangePublishedStatusView, LikeListCreateView,
    BookmarkListCreateView, ComplaintCreateView,
)

urlpatterns = [
    path('shop/categories/', ItemCategoriesListView.as_view(), name='item_categories'),
    path('shop/subcategories/', ItemCategoriesCreateView.as_view(), name='item_category_create'),
    path('shop/subcategories/<int:pk>/', ItemCategoryRetrieveUpdateDestroyView.as_view(), name='item_category_details'),
    path('shop/<int:pk>/subcategories/', OrganizationSubcategoriesView.as_view(), name='organization_subcategories'),

    path('shop/items/', ItemCreateView.as_view(), name='item_create'),
    path('shop/items/<int:pk>/', ItemRetrieveUpdateDestroyView.as_view(), name='item_details'),
    path('shop/doChangeItemPublishedStatus/', ItemChangePublishedStatusView.as_view(), name='item_published_status'),

    path('shop/feed/', FeedView.as_view(), name='shop_feed'),
    path('shop/organization_items/', OrganizationItemListView.as_view(), name='organization_items'),

    path('shop/likes/', LikeListCreateView.as_view(), name='like_list_create'),
    path('shop/bookmarks/', BookmarkListCreateView.as_view(), name='bookmark_list_create'),

    path('shop/complaints/', ComplaintCreateView.as_view(), name='complaint_create'),

    path('carts/', UserCartListView.as_view(), name='user_cart_list'),
    path('carts/<int:pk>/', UserCartRetrieveDestroyView.as_view(), name='user_cart_details'),
    path('carts/doChangeItemCount/', CartItemCountChangeView.as_view(), name='add_cart_item'),

    path('carts/<int:pk>/delivery/', OrderDeliveryView.as_view(), name='order_delivery'),
]
