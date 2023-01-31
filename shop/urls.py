from django.urls import path

from shop.views.cart_views import (
    CartItemCountChangeView, UserCartListView, OrderDeliveryView, TotalCartItemsCount,
    OrderSelfPickupView, UserCartRetrieveUpdateDestroyView, CartAnonymousCheckoutView, UpdateDeliveryToSendByCourierView
)
from shop.views.category_views import (
    ItemCategoryListView, ItemRentalCategoryListView, SubcategoryRetrieveUpdateDestroyView, ItemSubcategoryCreateView,
    OrganizationSubcategoryListView, NonEmptyCategoryListView, ItemCategoryRetrieveView,
    ItemCategoryAllSubcategoriesView, NonEmptyPartnerCategoryListView, NonEmptyPartnerSubcategoryListView
)
from shop.views.comment_views import CommentItemListCreateView, \
    CommentDestroyUpdateRetrievtView, CommentedItemsListView, CommentLike, CommentComplaintCreateView
from shop.views.feed_views import (
    FeedView, OrganizationItemListView, SubscriptionItemListView, HotlinkCollectionItemListView
)
from shop.views.item_views import (
    ItemCreateView, ItemRentalCreateView, ItemRetrieveUpdateDestroyView, ItemChangePublishedStatusView, LikeListCreateView,
    BookmarkListCreateView, ComplaintCreateView, TranslateItemTextView, SuggestSearchItem, PartnerShopItemsListView,
    RentItemPeriodCreateView
)

urlpatterns = [
    path('shop/categories/', ItemCategoryListView.as_view(), name='item_categories'),
    path('shop/categories/<int:pk>/', ItemCategoryRetrieveView.as_view(), name='item_category_details'),
    path('shop/categories/<int:pk>/all_subcategories/', ItemCategoryAllSubcategoriesView.as_view(),
         name='all_category_subcategories'),

    path('shop/rentals/categories/', ItemRentalCategoryListView.as_view(), name='rent_categories'),
    path('add_rental_period/<int:pk>/', RentItemPeriodCreateView.as_view(), name='add_rental_period'),

    path('shop/non_empty_categories/', NonEmptyCategoryListView.as_view(), name='non_empty_categories'),
    path('shop/non_empty_partner_categories/<int:pk>/', NonEmptyPartnerCategoryListView.as_view(), name='non_empty_partner_categories'),

    path('shop/subcategories/', ItemSubcategoryCreateView.as_view(), name='item_category_create'),
    path('shop/subcategories/<int:pk>/', SubcategoryRetrieveUpdateDestroyView.as_view(), name='subcategory_details'),
    path('shop/partner_subcategories/<int:pk>/', NonEmptyPartnerSubcategoryListView.as_view(), name='partner_subcategories'),

    path('shop/<int:pk>/subcategories/', OrganizationSubcategoryListView.as_view(), name='organization_subcategories'),

    path('shop/items/', ItemCreateView.as_view(), name='item_create'),
    path('shop/items/<str:pk>/', ItemRetrieveUpdateDestroyView.as_view(), name='item_details'),
    path('shop/doChangeItemPublishedStatus/', ItemChangePublishedStatusView.as_view(), name='item_published_status'),
    path('shop/translateItemText/', TranslateItemTextView.as_view(), name='translate_item_text'),

    path('shop/rentals/', ItemRentalCreateView.as_view(), name='rent_create'),

    path('shop/feed/', FeedView.as_view(), name='shop_feed'),
    path('search/item/', SuggestSearchItem.as_view(), name='suggest_item'),
    path('shop/organization_items/', OrganizationItemListView.as_view(), name='organization_items'),
    path('shop/subscription_items/', SubscriptionItemListView.as_view(), name='subscribed_organization_items'),
    path('shop/hotlink_items/<int:pk>/', HotlinkCollectionItemListView.as_view(), name='hotlink_collection_items'),

    path('shop/likes/', LikeListCreateView.as_view(), name='like_list_create'),
    path('shop/bookmarks/', BookmarkListCreateView.as_view(), name='bookmark_list_create'),

    path('shop/complaints/', ComplaintCreateView.as_view(), name='complaint_create'),

    path('carts/', UserCartListView.as_view(), name='user_cart_list'),
    path('carts/<int:pk>/', UserCartRetrieveUpdateDestroyView.as_view(), name='user_cart_details'),
    path('carts/doChangeItemCount/', CartItemCountChangeView.as_view(), name='add_cart_item'),
    path('carts/totalUserItemsCount/', TotalCartItemsCount.as_view(), name='all_cart_items_count'),
    path('carts/<int:pk>/delivery/', OrderDeliveryView.as_view(), name='order_delivery'),
    path('carts/<int:pk>/updateDelivery/', UpdateDeliveryToSendByCourierView.as_view(), name='order_delivery'),
    path('carts/<int:pk>/selfPickup/', OrderSelfPickupView.as_view(), name='order_self_pickup'),
    path('carts/<int:pk>/offline_checkout/', CartAnonymousCheckoutView.as_view(), name='cart_anonymous_checkout'),

    path('comments/item/<int:pk>/', CommentItemListCreateView.as_view(), name='comment_item_list'),
    path('comments/<int:pk>/', CommentDestroyUpdateRetrievtView.as_view(), name='comment_retrieve'),
    path('commented/items/', CommentedItemsListView.as_view(), name='commented_items'),
    path('comments/like/', CommentLike.as_view(), name='comment_like'),
    path('comments/complaints/', CommentComplaintCreateView.as_view(), name='comment_complaint_create'),

    path('partner_shop_items/<int:pk>/', PartnerShopItemsListView.as_view(), name='partner_shop_items'),
]
