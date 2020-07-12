from django.urls import path

from common.views import ImageCreateView, CountriesListView

urlpatterns = [
    path('files/', ImageCreateView.as_view(), name='images'),
    path('countries/', CountriesListView.as_view(), name='countries'),
]
