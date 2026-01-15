"""
WhatsApp Service Interface - Abstract base class for WhatsApp providers.

Supports multiple providers:
- WAHA (self-hosted) - primary
- Twilio - future backup
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class WhatsAppMessage:
    """Message to send via WhatsApp."""

    to: str  # Phone number (without @c.us suffix)
    text: str
    media_url: Optional[str] = None
    caption: Optional[str] = None


@dataclass
class WhatsAppResponse:
    """Response from WhatsApp service."""

    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None
    raw_response: Optional[Dict] = None


@dataclass
class WhatsAppIncomingMessage:
    """Parsed incoming message from webhook."""

    message_type: str  # "message" or "status"
    from_number: str
    text: str
    message_id: str
    has_media: bool = False
    media_url: Optional[str] = None
    timestamp: Optional[int] = None
    session_name: Optional[str] = None


class WhatsAppServiceInterface(ABC):
    """Abstract interface for WhatsApp services.

    All WhatsApp providers (WAHA, Twilio, etc.) must implement this interface.
    """

    @abstractmethod
    def send_message(self, message: WhatsAppMessage) -> WhatsAppResponse:
        """Send a text message.

        Args:
            message: WhatsAppMessage with recipient and text

        Returns:
            WhatsAppResponse with success status and message_id
        """
        pass

    @abstractmethod
    def send_photo(
        self,
        to: str,
        photo_url: str,
        caption: Optional[str] = None,
    ) -> WhatsAppResponse:
        """Send a photo with optional caption.

        Args:
            to: Recipient phone number
            photo_url: URL of the image
            caption: Optional caption text

        Returns:
            WhatsAppResponse with success status
        """
        pass

    @abstractmethod
    def get_qr_code(self) -> Optional[str]:
        """Get QR code for authentication (WAHA only).

        Returns:
            Base64 encoded QR image or URL, None if not applicable
        """
        pass

    @abstractmethod
    def check_connection(self) -> Dict[str, Any]:
        """Check connection status.

        Returns:
            Dict with status info (status, phone number, etc.)
        """
        pass

    @abstractmethod
    def is_healthy(self) -> bool:
        """Quick health check.

        Returns:
            True if service is available and responding
        """
        pass

    @abstractmethod
    def start_session(self) -> bool:
        """Start/initialize the session.

        Returns:
            True if session started successfully
        """
        pass

    @abstractmethod
    def stop_session(self) -> bool:
        """Stop the session.

        Returns:
            True if session stopped successfully
        """
        pass

    @abstractmethod
    def process_webhook(self, data: Dict) -> Optional[WhatsAppIncomingMessage]:
        """Process incoming webhook data.

        Args:
            data: Raw webhook payload

        Returns:
            Parsed WhatsAppIncomingMessage or None if not a message event
        """
        pass

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify webhook signature (optional, implemented by providers).

        Args:
            payload: Raw request body
            signature: Signature from header

        Returns:
            True if signature is valid
        """
        return True  # Default: no verification
