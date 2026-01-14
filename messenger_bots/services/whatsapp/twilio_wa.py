"""
Twilio WhatsApp Service - STUB for future implementation.

This is a placeholder that raises NotImplementedError for all methods.
When Twilio integration is needed, implement the methods here.

Docs: https://www.twilio.com/docs/whatsapp/api
"""

import logging
from typing import Any, Dict, Optional

from .base import (
    WhatsAppIncomingMessage,
    WhatsAppMessage,
    WhatsAppResponse,
    WhatsAppServiceInterface,
)

logger = logging.getLogger(__name__)


class TwilioWhatsAppService(WhatsAppServiceInterface):
    """Twilio WhatsApp service - STUB.

    This is a placeholder for future Twilio integration.
    All methods raise NotImplementedError except:
    - get_qr_code() returns None (Twilio doesn't use QR)
    - is_healthy() returns False (not implemented)

    To implement Twilio:
    1. pip install twilio
    2. Add TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN to settings
    3. Implement methods in this class
    """

    def __init__(self, whatsapp_bot):
        """Initialize Twilio service.

        Args:
            whatsapp_bot: WhatsAppBot model instance
        """
        self.bot = whatsapp_bot
        # TODO: Initialize Twilio client when implementing
        # from twilio.rest import Client
        # self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        # self.from_number = whatsapp_bot.twilio_phone_number

    def send_message(self, message: WhatsAppMessage) -> WhatsAppResponse:
        """Send text message via Twilio - NOT IMPLEMENTED."""
        raise NotImplementedError(
            "Twilio WhatsApp integration not implemented yet. "
            "Use WAHA as the primary provider."
        )

    def send_photo(
        self,
        to: str,
        photo_url: str,
        caption: Optional[str] = None,
    ) -> WhatsAppResponse:
        """Send photo via Twilio - NOT IMPLEMENTED."""
        raise NotImplementedError(
            "Twilio WhatsApp integration not implemented yet. "
            "Use WAHA as the primary provider."
        )

    def get_qr_code(self) -> Optional[str]:
        """Twilio doesn't use QR codes - always returns None."""
        return None

    def check_connection(self) -> Dict[str, Any]:
        """Check Twilio connection - NOT IMPLEMENTED."""
        raise NotImplementedError(
            "Twilio WhatsApp integration not implemented yet. "
            "Use WAHA as the primary provider."
        )

    def is_healthy(self) -> bool:
        """Twilio not implemented - always returns False."""
        return False

    def start_session(self) -> bool:
        """Twilio doesn't need session start - NOT IMPLEMENTED."""
        raise NotImplementedError(
            "Twilio WhatsApp integration not implemented yet. "
            "Use WAHA as the primary provider."
        )

    def stop_session(self) -> bool:
        """Twilio doesn't have sessions - NOT IMPLEMENTED."""
        raise NotImplementedError(
            "Twilio WhatsApp integration not implemented yet. "
            "Use WAHA as the primary provider."
        )

    def process_webhook(self, data: Dict) -> Optional[WhatsAppIncomingMessage]:
        """Process Twilio webhook - NOT IMPLEMENTED."""
        raise NotImplementedError(
            "Twilio WhatsApp integration not implemented yet. "
            "Use WAHA as the primary provider."
        )

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify Twilio signature - NOT IMPLEMENTED."""
        raise NotImplementedError(
            "Twilio WhatsApp integration not implemented yet. "
            "Use WAHA as the primary provider."
        )


# ==============================================================================
# IMPLEMENTATION GUIDE (for future reference)
# ==============================================================================
#
# When implementing Twilio, use the following structure:
#
# from django.conf import settings
# from twilio.rest import Client
# from twilio.request_validator import RequestValidator
#
# class TwilioWhatsAppService(WhatsAppServiceInterface):
#     def __init__(self, whatsapp_bot):
#         self.bot = whatsapp_bot
#         self.account_sid = settings.TWILIO_ACCOUNT_SID
#         self.auth_token = settings.TWILIO_AUTH_TOKEN
#         self.from_number = whatsapp_bot.twilio_phone_number
#         self.client = Client(self.account_sid, self.auth_token)
#         self.validator = RequestValidator(self.auth_token)
#
#     def send_message(self, message: WhatsAppMessage) -> WhatsAppResponse:
#         result = self.client.messages.create(
#             body=message.text,
#             from_=f"whatsapp:{self.from_number}",
#             to=f"whatsapp:+{message.to}",
#         )
#         return WhatsAppResponse(success=True, message_id=result.sid)
#
#     def verify_webhook_signature(self, url: str, params: Dict, signature: str):
#         return self.validator.validate(url, params, signature)
#
#     def process_webhook(self, data: Dict) -> Optional[WhatsAppIncomingMessage]:
#         return WhatsAppIncomingMessage(
#             message_type="message",
#             from_number=data.get("From", "").replace("whatsapp:+", ""),
#             text=data.get("Body", ""),
#             message_id=data.get("MessageSid", ""),
#             has_media=int(data.get("NumMedia", 0)) > 0,
#         )
# ==============================================================================
