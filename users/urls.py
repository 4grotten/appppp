from django.urls import path

from users.views import (
    RegisterAuthAPIView, VerifyTemporaryCodeAPIView,
    ResendTemporaryCodeAPIView, LoginAPIView, LogoutAPIView,
    ProfileInitialAPIView, SetPasswordAPIView, UserChangePasswordAPIView,
    ForgotPasswordAPIView, CurrentUserAPIView, UserPhonesListAPIView,
    UserPhoneNumbersUpdateAPIView, UserSocialNetworksListAPIView, UserSocialNetworksUpdateAPIView,
    ValidateOldNumberAPIView, ChangeAndVerifyNewNumber, SendCodeToNewNumberAPIView, GetEmailUserAPIView,
    MyOwnTokenListView, MyOwnTokenRetrieveDestroyView, DestroyAllTokens, AuthorisationHistoryListView,
    MyOwnTokenChangeExpiredTimeView, DeactivateUserProfile
)

urlpatterns = [
    path('register_auth/', RegisterAuthAPIView.as_view(), name='register_auth'),
    path('verify_code/', VerifyTemporaryCodeAPIView.as_view(), name='verify_code'),
    path('resend_code/', ResendTemporaryCodeAPIView.as_view(), name='resend_code'),
    path('init_profile/', ProfileInitialAPIView.as_view(), name='init_profile'),
    path('set_password/', SetPasswordAPIView.as_view(), name='set_password'),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('logout/', LogoutAPIView.as_view(), name='logout'),
    path('users/doChangePassword/', UserChangePasswordAPIView.as_view(), name='change_password'),
    path('users/forgot_password/', ForgotPasswordAPIView.as_view(), name='forgot_password'),
    path('users/me/', CurrentUserAPIView.as_view(), name='me'),
    path('users/<int:pk>/phone_numbers/', UserPhonesListAPIView.as_view(), name='user_phones'),
    path('users/phone_numbers/', UserPhoneNumbersUpdateAPIView.as_view(), name='set_user_phones'),
    path('users/<int:pk>/social_networks/', UserSocialNetworksListAPIView.as_view(), name='user_networks'),
    path('users/social_networks/', UserSocialNetworksUpdateAPIView.as_view(), name='set_user_networks'),
    path('users/doValidateOldNumber/', ValidateOldNumberAPIView.as_view(), name='validate_old_number'),
    path('users/doSendCode/', SendCodeToNewNumberAPIView.as_view(), name='send_code_to_new_number'),
    path('users/doChangeAndVerifyNewNumber/', ChangeAndVerifyNewNumber.as_view(), name='change_and_verify_new_number'),
    path('users/get_email/', GetEmailUserAPIView.as_view(), name='get_email_by_phone_number'),
    path('users/get_active_devices/', MyOwnTokenListView.as_view(), name='get_active_devices'),
    path('users/get_or_deactivate_token/<int:pk>/', MyOwnTokenRetrieveDestroyView.as_view(), name='get_token_detail'),
    path('users/deactivate_all_tokens/', DestroyAllTokens.as_view(), name='deactivate_all_tokens'),
    path('users/authorisation_history/', AuthorisationHistoryListView.as_view(), name='deactivate_all_tokens'),
    path('users/change_token_expired_time/<int:pk>/', MyOwnTokenChangeExpiredTimeView.as_view(), name='change_token_expired_time'),

    path('users/deactivate/', DeactivateUserProfile.as_view(), name='deactivate_user_profile'),
]
