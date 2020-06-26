from django.urls import path

from common.views import FileCreateView


urlpatterns = [
    path('files/', FileCreateView.as_view(), name='files')
]
