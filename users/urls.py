from django.urls import path

from users.views import RegisterAuthAPIView

urlpatterns = [
    path('register_auth/', RegisterAuthAPIView.as_view(), name='register_auth')
]
