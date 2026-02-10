"""DRF API Views for OTP Bot service."""

import logging

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from users.models import User
from users.services import MyOwnTokenService

from .permissions import IsOTPAdmin
from .serializers import (
    SendOTPSerializer,
    VerifyOTPSerializer,
)
from .services.otp_service import (
    BotNotConnectedError,
    CooldownError,
    OTPService,
    OTPServiceError,
    RateLimitError,
)

logger = logging.getLogger(__name__)


# --- Bot Management (Admin only, API Key required) ---


class OTPBotInitializeAPIView(APIView):
    """Initialize OTP bot: create singleton + start WAHA session."""

    permission_classes = [IsOTPAdmin]

    def post(self, request):
        logger.info("[OTP_API] POST /otp-bot/initialize/")
        service = OTPService()
        bot = service.initialize_bot()
        return Response(
            {
                "is_initialized": True,
                "status": bot.status,
                "phone_number": bot.phone_number,
                "session_name": bot.waha_session_name,
            }
        )


class OTPBotStatusAPIView(APIView):
    """Get OTP bot status (syncs with WAHA)."""

    permission_classes = [IsOTPAdmin]

    def get(self, request):
        service = OTPService()
        bot = service.get_bot_status()
        if not bot:
            return Response(
                {
                    "is_initialized": False,
                    "status": "not_initialized",
                    "phone_number": None,
                    "session_name": None,
                }
            )
        return Response(
            {
                "is_initialized": True,
                "status": bot.status,
                "phone_number": bot.phone_number,
                "session_name": bot.waha_session_name,
            }
        )


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
            return Response(
                {
                    "qr_code": None,
                    "message": "Already connected",
                    "phone_number": bot.phone_number,
                }
            )
        qr = service.get_qr_code()
        return Response(
            {
                "qr_code": qr,
                "message": (
                    "Scan QR with WhatsApp" if qr else "QR not available, try again"
                ),
            }
        )


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


class CheckPhoneAPIView(APIView):
    """Check if phone number exists in the system (for routing new vs existing users)."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        phone = serializer.validated_data["phone_number"]
        exists = User.objects.filter(phone_number=phone).exists()
        logger.info(
            f"[OTP_API] POST /otp/check-phone/ phone={phone[:7]}*** exists={exists}"
        )

        return Response({"exists": exists})


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
            return Response(
                {
                    "otp_id": result.otp_id,
                    "phone_number": result.phone_number,
                    "expires_at": result.expires_at,
                    "sent": result.sent,
                }
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


class VerifyOTPAPIView(APIView):
    """Verify an OTP code. On success, creates/finds user and returns auth token."""

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

        if not result.is_valid:
            return Response(
                {
                    "is_valid": False,
                    "error": result.error,
                    "token": None,
                    "is_new_user": None,
                }
            )

        # OTP verified — get or create user and issue token
        username = serializer.validated_data.get("username")
        password = serializer.validated_data.get("password")

        user, created = User.objects.get_or_create(
            phone_number=phone,
            defaults={"is_new_user": True},
        )

        if created:
            # New user registration — require username and password
            if not username or not password:
                user.delete()
                return Response(
                    {
                        "is_valid": True,
                        "error": "Username and password are required for registration",
                        "token": None,
                        "is_new_user": True,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Check username uniqueness
            if User.objects.filter(username=username).exists():
                user.delete()
                return Response(
                    {
                        "is_valid": True,
                        "error": "Username is already taken",
                        "token": None,
                        "is_new_user": True,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user.username = username
            user.set_password(password)
            user.save(update_fields=["username", "password"])
            logger.info(
                f"[OTP_API] New user registered: {phone[:7]}*** username={username}"
            )

        is_new_user = user.is_new_user
        token = MyOwnTokenService.get_or_create_token(user=user, request=request)
        logger.info(
            f"[OTP_API] Token issued for {phone[:7]}*** (new_user={is_new_user})"
        )

        # Try to link with EasyCard profile for user synchronization
        try:
            from easycard_integration.services import EasyCardDataService
            from .models import UserEasyCardMapping

            easycard_data = EasyCardDataService.get_user_financial_data(phone)
            if easycard_data.is_registered and easycard_data.user_id:
                UserEasyCardMapping.objects.update_or_create(
                    apofiz_user=user,
                    defaults={
                        "easycard_user_id": easycard_data.user_id,
                        "phone_number": phone,
                    },
                )
                logger.info(
                    f"[OTP_API] Linked Apofiz user {user.id} "
                    f"with EasyCard {easycard_data.user_id[:8]}..."
                )
        except Exception as e:
            # Don't fail verification if linking fails
            logger.warning(f"[OTP_API] Failed to link EasyCard profile: {e}")

        # Send welcome message to new users via OTP Bot
        if is_new_user:
            from .tasks import send_welcome_message_task
            send_welcome_message_task.delay(phone_number=phone)
            logger.info(f"[OTP_API] Welcome message task queued for {phone[:7]}***")

        return Response(
            {
                "is_valid": True,
                "error": None,
                "token": token.key,
                "is_new_user": is_new_user,
            }
        )


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
            return Response(
                {
                    "otp_id": result.otp_id,
                    "phone_number": result.phone_number,
                    "expires_at": result.expires_at,
                    "sent": result.sent,
                }
            )
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


# --- Webhook (WAHA incoming messages) ---


class OTPBotWebhookView(APIView):
    """Receive incoming WhatsApp messages from WAHA.

    NOTE: This endpoint is now a NO-OP. All message routing goes through
    messenger_bots webhook to avoid duplicate processing.
    The messenger_bots webhook routes new users to OTPBotWebhookHandler.

    This endpoint exists only for backwards compatibility with WAHA
    webhook configuration. It will be removed once WAHA config is updated.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        # NO-OP: All processing done via messenger_bots webhook
        # Just acknowledge receipt to prevent WAHA retries
        return Response({"status": "ok"})
