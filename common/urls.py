from django.urls import path

from common.views import ImageCreateView, CountriesListView, CountryCitySearchView, WatermarkImageCreateView, \
    ImageCreateFromUrlView

urlpatterns = [
    path('files/', ImageCreateView.as_view(), name='images'),
    path('save_image_from_url/', ImageCreateFromUrlView.as_view(), name='image_from_url'),
    path('watermarked_images/', WatermarkImageCreateView.as_view(), name='watermarked_images'),
    path('countries/', CountriesListView.as_view(), name='countries'),
    path('countries_and_cities/', CountryCitySearchView.as_view(), name='countries_cities_search'),
]
