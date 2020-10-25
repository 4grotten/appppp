from django.urls import path

from common.views import ImageCreateView, CountriesListView, CountryCitySearchView, WatermarkImageCreateView

urlpatterns = [
    path('files/', ImageCreateView.as_view(), name='images'),
    path('watermarked_images/', WatermarkImageCreateView.as_view(), name='watermarked_images'),
    path('countries/', CountriesListView.as_view(), name='countries'),
    path('countries_and_cities/', CountryCitySearchView.as_view(), name='countries_cities_search'),
]
