from django.urls import path

from shop.views.category_views import (
    ItemCategoriesListView, ItemCategoryRetrieveUpdateDestroyView, ItemCategoriesCreateView
)

urlpatterns = [
    path('shop/categories/', ItemCategoriesListView.as_view(), name='item_categories'),
    path('shop/subcategories/', ItemCategoriesCreateView.as_view(), name='item_category_create'),
    path('shop/subcategories/<int:pk>/', ItemCategoryRetrieveUpdateDestroyView.as_view(), name='item_category_details'),
]
