from django.urls import path

from shop.views.cart_views import (
    CartItemCountChangeView, UserCartListView, OrderDeliveryView, TotalCartItemsCount,
    OrderSelfPickupView, UserCartRetrieveUpdateDestroyView, CartAnonymousCheckoutView
)
from shop.views.category_views import (
    ItemCategoryListView, SubcategoryRetrieveUpdateDestroyView, ItemSubcategoryCreateView,
    OrganizationSubcategoryListView, NonEmptyCategoryListView, ItemCategoryRetrieveView,
    ItemCategoryAllSubcategoriesView
)
from shop.views.feed_views import FeedView, OrganizationItemListView, SubscriptionItemListView
from shop.views.item_views import (
    ItemCreateView, ItemRetrieveUpdateDestroyView, ItemChangePublishedStatusView, LikeListCreateView,
    BookmarkListCreateView, ComplaintCreateView,
)

urlpatterns = [
    path('shop/categories/', ItemCategoryListView.as_view(), name='item_categories'),
    path('shop/categories/<int:pk>/', ItemCategoryRetrieveView.as_view(), name='item_category_details'),
    path('shop/categories/<int:pk>/all_subcategories/', ItemCategoryAllSubcategoriesView.as_view(),
         name='all_category_subcategories'),

    path('shop/non_empty_categories/', NonEmptyCategoryListView.as_view(), name='non_empty_categories'),
    path('shop/subcategories/', ItemSubcategoryCreateView.as_view(), name='item_category_create'),
    path('shop/subcategories/<int:pk>/', SubcategoryRetrieveUpdateDestroyView.as_view(), name='subcategory_details'),
    path('shop/<int:pk>/subcategories/', OrganizationSubcategoryListView.as_view(), name='organization_subcategories'),

    path('shop/items/', ItemCreateView.as_view(), name='item_create'),
    path('shop/items/<str:pk>/', ItemRetrieveUpdateDestroyView.as_view(), name='item_details'),
    path('shop/doChangeItemPublishedStatus/', ItemChangePublishedStatusView.as_view(), name='item_published_status'),

    path('shop/feed/', FeedView.as_view(), name='shop_feed'),
    path('shop/organization_items/', OrganizationItemListView.as_view(), name='organization_items'),
    path('shop/subscription_items/', SubscriptionItemListView.as_view(), name='subscribed_organization_items'),

    path('shop/likes/', LikeListCreateView.as_view(), name='like_list_create'),
    path('shop/bookmarks/', BookmarkListCreateView.as_view(), name='bookmark_list_create'),

    path('shop/complaints/', ComplaintCreateView.as_view(), name='complaint_create'),

    path('carts/', UserCartListView.as_view(), name='user_cart_list'),
    path('carts/<int:pk>/', UserCartRetrieveUpdateDestroyView.as_view(), name='user_cart_details'),
    path('carts/doChangeItemCount/', CartItemCountChangeView.as_view(), name='add_cart_item'),
    path('carts/totalUserItemsCount/', TotalCartItemsCount.as_view(), name='all_cart_items_count'),
    path('carts/<int:pk>/delivery/', OrderDeliveryView.as_view(), name='order_delivery'),
    path('carts/<int:pk>/selfPickup/', OrderSelfPickupView.as_view(), name='order_self_pickup'),
    path('carts/<int:pk>/offline_checkout/', CartAnonymousCheckoutView.as_view(), name='cart_anonymous_checkout'),
]
