from django.urls import path

from common.views import ImageCreateView, CountriesListView, CountryCitySearchView

urlpatterns = [
    path('files/', ImageCreateView.as_view(), name='images'),
    path('countries/', CountriesListView.as_view(), name='countries'),
    path('countries_and_cities/', CountryCitySearchView.as_view(), name='countries_cities_search'),
]
