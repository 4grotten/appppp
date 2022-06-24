from django.urls import path

from stock.views import FormatCriteriaListView, SizeByFormatListView, CriteriaSubcategoryListView, CreateStokeCartView, \
    AddSizeQuantityView

urlpatterns = [
    path('criteria_by_subcategory/<int:pk>/', CriteriaSubcategoryListView.as_view(), name='criteria_by_subcategory'),
    path('format_by_criteria/<int:pk>/', FormatCriteriaListView.as_view(), name='format_by_criteria'),
    path('size_by_format/<int:pk>/', SizeByFormatListView.as_view(), name='size_by_format'),
    path('stock_cart/<int:pk>/', CreateStokeCartView.as_view(), name='stock_cart_create'),
    path('add_size_count/<int:pk>/', AddSizeQuantityView.as_view(), name='add_size_count'),
]
