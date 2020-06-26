from django.urls import path

from users.views import RegisterAuthAPIView, VerifyTemporaryCodeAPIView

urlpatterns = [
    path('register_auth/', RegisterAuthAPIView.as_view(), name='register_auth'),
    path('verify_code/', VerifyTemporaryCodeAPIView.as_view(), name='verify_code')
]
