from django.urls import path

from shop.views.category_views import ItemCategoriesListView

urlpatterns = [
    path('shop/categories/', ItemCategoriesListView.as_view(), name='item_categories'),
]
