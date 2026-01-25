from django.urls import path

from otp_bot.views import (
    OTPBotInitializeAPIView,
    OTPBotStatusAPIView,
    OTPBotQRCodeAPIView,
    OTPBotDisconnectAPIView,
    OTPBotWebhookView,
    CheckPhoneAPIView,
    SendOTPAPIView,
    VerifyOTPAPIView,
    ResendOTPAPIView,
)

urlpatterns = [
    # Bot management (admin, API key required)
    path("otp-bot/initialize/", OTPBotInitializeAPIView.as_view(), name="otp-bot-initialize"),
    path("otp-bot/status/", OTPBotStatusAPIView.as_view(), name="otp-bot-status"),
    path("otp-bot/qr/", OTPBotQRCodeAPIView.as_view(), name="otp-bot-qr"),
    path("otp-bot/disconnect/", OTPBotDisconnectAPIView.as_view(), name="otp-bot-disconnect"),
    # Webhook (WAHA callback, no auth)
    path("otp-bot/webhook/", OTPBotWebhookView.as_view(), name="otp-bot-webhook"),

    # OTP operations (public, rate-limited)
    path("otp/check-phone/", CheckPhoneAPIView.as_view(), name="otp-check-phone"),
    path("otp/send/", SendOTPAPIView.as_view(), name="otp-send"),
    path("otp/verify/", VerifyOTPAPIView.as_view(), name="otp-verify"),
    path("otp/resend/", ResendOTPAPIView.as_view(), name="otp-resend"),
]
