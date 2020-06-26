from django.urls import path

from users.views import RegisterAuthAPIView, VerifyTemporaryCodeAPIView, ResendTemporaryCodeAPIView

urlpatterns = [
    path('register_auth/', RegisterAuthAPIView.as_view(), name='register_auth'),
    path('verify_code/', VerifyTemporaryCodeAPIView.as_view(), name='verify_code'),
    path('resend_code/', ResendTemporaryCodeAPIView.as_view(), name='resend_code')
]
