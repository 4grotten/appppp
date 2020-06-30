from django.urls import path

from users.views import (
    RegisterAuthAPIView, VerifyTemporaryCodeAPIView,
    ResendTemporaryCodeAPIView, LoginAPIView,
    ProfileInitialAPIView, SetPasswordAPIView, UserChangePasswordAPIView, ForgotPasswordAPIView
)

urlpatterns = [
    path('register_auth/', RegisterAuthAPIView.as_view(), name='register_auth'),
    path('verify_code/', VerifyTemporaryCodeAPIView.as_view(), name='verify_code'),
    path('resend_code/', ResendTemporaryCodeAPIView.as_view(), name='resend_code'),
    path('init_profile/', ProfileInitialAPIView.as_view(), name='init_profile'),
    path('set_password/', SetPasswordAPIView.as_view(), name='set_password'),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('users/doChangePassword/', UserChangePasswordAPIView.as_view(), name='change_password'),
    path('users/forgot_password/', ForgotPasswordAPIView.as_view(), name='forgot_password')
]
