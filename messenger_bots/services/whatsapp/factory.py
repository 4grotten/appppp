"""
WhatsApp Service Factory.

Creates appropriate WhatsApp service based on provider setting.
Currently only WAHA is fully implemented; Twilio is a stub for future use.
"""

import logging
from typing import TYPE_CHECKING

from messenger_bots.models import WhatsAppProvider

from .base import WhatsAppServiceInterface
from .twilio_wa import TwilioWhatsAppService
from .waha import WAHAService

if TYPE_CHECKING:
    from messenger_bots.models import WhatsAppBot

logger = logging.getLogger(__name__)


class WhatsAppServiceFactory:
    """Factory for creating WhatsApp service instances.

    Usage:
        service = WhatsAppServiceFactory.get_service(whatsapp_bot)
        response = service.send_message(message)
    """

    @classmethod
    def get_service(cls, whatsapp_bot: "WhatsAppBot") -> WhatsAppServiceInterface:
        """Get WhatsApp service based on bot's provider setting.

        Args:
            whatsapp_bot: WhatsAppBot model instance

        Returns:
            Appropriate service implementation (WAHAService or TwilioWhatsAppService)

        Note:
            Currently only WAHA is fully implemented.
            Twilio will raise NotImplementedError for most operations.
        """
        if whatsapp_bot.provider == WhatsAppProvider.TWILIO:
            logger.warning(
                f"Twilio provider requested for org {whatsapp_bot.organization_id}, "
                "but Twilio is not implemented. Will raise errors on operations."
            )
            return TwilioWhatsAppService(whatsapp_bot)

        # Default to WAHA (primary provider)
        return WAHAService(whatsapp_bot)

    @classmethod
    def create_waha_service(cls, whatsapp_bot: "WhatsAppBot") -> WAHAService:
        """Explicitly create WAHA service (ignores provider setting).

        Args:
            whatsapp_bot: WhatsAppBot model instance

        Returns:
            WAHAService instance
        """
        return WAHAService(whatsapp_bot)


# ==============================================================================
# FUTURE: Failover support
# ==============================================================================
# When Twilio is implemented, add failover logic:
#
# class WhatsAppServiceWithFailover(WhatsAppServiceInterface):
#     """Wrapper that handles failover between providers."""
#
#     def __init__(self, whatsapp_bot: "WhatsAppBot"):
#         self.bot = whatsapp_bot
#         self.primary = WAHAService(whatsapp_bot)
#         self.fallback = TwilioWhatsAppService(whatsapp_bot)
#
#     def send_message(self, message: WhatsAppMessage) -> WhatsAppResponse:
#         try:
#             if self.primary.is_healthy():
#                 return self.primary.send_message(message)
#         except Exception as e:
#             logger.warning(f"Primary (WAHA) failed: {e}")
#
#         # Failover to Twilio
#         if self.bot.auto_failover:
#             logger.info("Failing over to Twilio")
#             return self.fallback.send_message(message)
#
#         return WhatsAppResponse(success=False, error="Primary provider unavailable")
# ==============================================================================
