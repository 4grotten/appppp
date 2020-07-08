from django.urls import path

from common.views import FileCreateView, CountriesListView

urlpatterns = [
    path('files/', FileCreateView.as_view(), name='files'),
    path('countries/', CountriesListView.as_view(), name='countries'),
]
