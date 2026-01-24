"""DRF API Views for OTP Bot service."""

import logging

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    SendOTPSerializer,
    VerifyOTPSerializer,
)
from .services.otp_service import (
    OTPService,
    OTPServiceError,
    RateLimitError,
    CooldownError,
    BotNotConnectedError,
)
from .permissions import IsOTPAdmin

logger = logging.getLogger(__name__)


# --- Bot Management (Admin only, API Key required) ---


class OTPBotInitializeAPIView(APIView):
    """Initialize OTP bot: create singleton + start WAHA session."""

    permission_classes = [IsOTPAdmin]

    def post(self, request):
        logger.info("[OTP_API] POST /otp-bot/initialize/")
        service = OTPService()
        bot = service.initialize_bot()
        return Response({
            "is_initialized": True,
            "status": bot.status,
            "phone_number": bot.phone_number,
            "session_name": bot.waha_session_name,
        })


class OTPBotStatusAPIView(APIView):
    """Get OTP bot status (syncs with WAHA)."""

    permission_classes = [IsOTPAdmin]

    def get(self, request):
        service = OTPService()
        bot = service.get_bot_status()
        if not bot:
            return Response({
                "is_initialized": False,
                "status": "not_initialized",
                "phone_number": None,
                "session_name": None,
            })
        return Response({
            "is_initialized": True,
            "status": bot.status,
            "phone_number": bot.phone_number,
            "session_name": bot.waha_session_name,
        })


class OTPBotQRCodeAPIView(APIView):
    """Get QR code for OTP bot authentication."""

    permission_classes = [IsOTPAdmin]

    def get(self, request):
        service = OTPService()
        bot = service.get_bot_status()
        if not bot:
            return Response(
                {"error": "Bot not initialized. Call POST /otp-bot/initialize/ first."},
                status=status.HTTP_404_NOT_FOUND,
            )
        if bot.is_connected:
            return Response({
                "qr_code": None,
                "message": "Already connected",
                "phone_number": bot.phone_number,
            })
        qr = service.get_qr_code()
        return Response({
            "qr_code": qr,
            "message": "Scan QR with WhatsApp" if qr else "QR not available, try again",
        })


class OTPBotDisconnectAPIView(APIView):
    """Disconnect OTP bot session."""

    permission_classes = [IsOTPAdmin]

    def delete(self, request):
        logger.info("[OTP_API] DELETE /otp-bot/disconnect/")
        service = OTPService()
        success = service.disconnect_bot()
        if success:
            return Response({"success": True})
        return Response(
            {"error": "Bot not found or already disconnected"},
            status=status.HTTP_404_NOT_FOUND,
        )


# --- OTP Operations (Public, protected by rate limiting) ---


class SendOTPAPIView(APIView):
    """Send OTP code to a phone number."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        phone = serializer.validated_data["phone_number"]
        logger.info(f"[OTP_API] POST /otp/send/ phone={phone[:7]}***")

        service = OTPService()
        try:
            result = service.send_otp(phone)
            return Response({
                "otp_id": result.otp_id,
                "phone_number": result.phone_number,
                "expires_at": result.expires_at,
                "sent": result.sent,
            })
        except BotNotConnectedError:
            return Response(
                {"error": "OTP service temporarily unavailable"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except RateLimitError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        except OTPServiceError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class VerifyOTPAPIView(APIView):
    """Verify an OTP code."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        phone = serializer.validated_data["phone_number"]
        code = serializer.validated_data["code"]
        logger.info(f"[OTP_API] POST /otp/verify/ phone={phone[:7]}***")

        service = OTPService()
        result = service.verify_otp(phone, code)
        return Response({
            "is_valid": result.is_valid,
            "error": result.error,
        })


class ResendOTPAPIView(APIView):
    """Resend OTP with cooldown enforcement."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        phone = serializer.validated_data["phone_number"]
        logger.info(f"[OTP_API] POST /otp/resend/ phone={phone[:7]}***")

        service = OTPService()
        try:
            result = service.resend_otp(phone)
            return Response({
                "otp_id": result.otp_id,
                "phone_number": result.phone_number,
                "expires_at": result.expires_at,
                "sent": result.sent,
            })
        except CooldownError as e:
            return Response(
                {"error": str(e), "seconds_remaining": e.seconds_remaining},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        except BotNotConnectedError:
            return Response(
                {"error": "OTP service temporarily unavailable"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except RateLimitError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        except OTPServiceError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
