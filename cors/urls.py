from django.urls import path

from cors.views import CorsView

urlpatterns = [
    path('cors/', CorsView.as_view(), name='cors'),
]
