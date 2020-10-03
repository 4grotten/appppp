from django.urls import path

from shop.views.category_views import (
    ItemCategoriesListView, ItemCategoryRetrieveUpdateDestroyView, ItemCategoriesCreateView
)
from shop.views.feed_views import FeedView, OrganizationItemListView
from shop.views.item_views import ItemCreateView, ItemRetrieveUpdateDestroyView, ItemChangePublishedStatusView

urlpatterns = [
    path('shop/categories/', ItemCategoriesListView.as_view(), name='item_categories'),
    path('shop/subcategories/', ItemCategoriesCreateView.as_view(), name='item_category_create'),
    path('shop/subcategories/<int:pk>/', ItemCategoryRetrieveUpdateDestroyView.as_view(), name='item_category_details'),

    path('shop/items/', ItemCreateView.as_view(), name='item_create'),
    path('shop/items/<int:pk>/', ItemRetrieveUpdateDestroyView.as_view(), name='item_details'),
    path('shop/doChangeItemPublishedStatus/', ItemChangePublishedStatusView.as_view(), name='item_published_status'),

    path('shop/feed/', FeedView.as_view(), name='shop_feed'),
    path('shop/organization_items/', OrganizationItemListView.as_view(), name='organization_items'),
]
