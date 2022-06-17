from django.urls import path

from stock.views import FormatCriteriaListView, SizeByFormatView

urlpatterns = [
    path('format_criteria/', FormatCriteriaListView.as_view(), name='format_criteria'),
    path('size_by_format/<int:pk>/', SizeByFormatView.as_view(), name='size_by_format'),
]
