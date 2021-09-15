from django.urls import path

from cors.views import CorsView

urlpatterns = [
    path('shlyuzer/', CorsView.as_view(), name='cors'),
]
