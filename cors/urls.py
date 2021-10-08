from django.urls import path

from cors.views import CorsView, IpLocation

urlpatterns = [
    path('shlyuzer/', CorsView.as_view(), name='cors'),
    path('extreme-ip/', IpLocation.as_view(), name='ip'),
]
