"""
WAHA (WhatsApp HTTP API) Service Implementation.

Self-hosted WhatsApp API using NOWEB engine for low memory footprint.
Docs: https://waha.devlike.pro/docs/
"""

import hashlib
import hmac
import logging
from typing import Any, Dict, Optional

import requests
from django.conf import settings

from .base import (
    WhatsAppIncomingMessage,
    WhatsAppMessage,
    WhatsAppResponse,
    WhatsAppServiceInterface,
)

logger = logging.getLogger(__name__)


class WAHAService(WhatsAppServiceInterface):
    """WAHA (WhatsApp HTTP API) service implementation.

    Uses NOWEB engine for optimal RAM usage (~100-200MB).
    """

    def __init__(self, whatsapp_bot):
        """Initialize WAHA service.

        Args:
            whatsapp_bot: WhatsAppBot model instance
        """
        self.bot = whatsapp_bot
        self.base_url = getattr(settings, "WAHA_BASE_URL", "http://waha:3000")
        self.api_key = getattr(settings, "WAHA_API_KEY", "")
        self.webhook_secret = getattr(settings, "WAHA_WEBHOOK_SECRET", "")
        # WAHA Core (free) only supports "default" session
        # For multiple sessions, need WAHA Plus ($19/month)
        # WAHA PLUS: uncomment next line and comment the one below
        # self.session_name = whatsapp_bot.waha_session_name or f"org_{whatsapp_bot.organization_id}"
        self.session_name = whatsapp_bot.waha_session_name or "default"

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for WAHA API requests."""
        return {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json",
        }

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        timeout: int = 30,
    ) -> Dict:
        """Make HTTP request to WAHA API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., /api/sessions)
            data: Request body for POST/PUT
            timeout: Request timeout in seconds

        Returns:
            Response JSON as dict

        Raises:
            requests.exceptions.RequestException: On network errors
        """
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self._get_headers(),
                json=data,
                timeout=timeout,
            )
            response.raise_for_status()
            return response.json() if response.text else {}
        except requests.exceptions.Timeout:
            logger.error(f"WAHA request timeout: {endpoint}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"WAHA request error: {e}")
            raise

    def is_healthy(self) -> bool:
        """Check if WAHA service is available."""
        try:
            response = requests.get(
                f"{self.base_url}/api/health",
                headers=self._get_headers(),
                timeout=5,
            )
            return response.status_code == 200
        except Exception:
            return False

    def start_session(self) -> bool:
        """Create and start WAHA session.

        Creates a new session if it doesn't exist, then starts it.
        Configures webhook for this session.
        """
        try:
            backend_url = getattr(settings, "BACKEND_URL", "https://api.appofiz.com")

            # Create session with webhook config
            self._make_request(
                "POST",
                "/api/sessions",
                {
                    "name": self.session_name,
                    "config": {
                        "webhook": {
                            "url": f"{backend_url}/api/v1/messenger-bots/whatsapp/waha/webhook/",
                            "events": ["message", "session.status"],
                            "hmac": {"key": self.webhook_secret},
                        }
                    },
                },
            )

            # Start the session
            self._make_request("POST", f"/api/sessions/{self.session_name}/start")

            logger.info(f"WAHA session started: {self.session_name}")
            return True

        except requests.exceptions.HTTPError as e:
            # Session might already exist
            if e.response.status_code == 409:
                logger.info(f"WAHA session already exists: {self.session_name}")
                # Try to start it anyway
                try:
                    self._make_request(
                        "POST", f"/api/sessions/{self.session_name}/start"
                    )
                    return True
                except Exception:
                    pass
            logger.error(f"Failed to start WAHA session: {e}")
            self._update_bot_error(str(e))
            return False

        except Exception as e:
            logger.error(f"Failed to start WAHA session: {e}")
            self._update_bot_error(str(e))
            return False

    def stop_session(self) -> bool:
        """Stop WAHA session."""
        try:
            self._make_request("POST", f"/api/sessions/{self.session_name}/stop")
            logger.info(f"WAHA session stopped: {self.session_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to stop WAHA session: {e}")
            return False

    def get_qr_code(self) -> Optional[str]:
        """Get QR code for WhatsApp authentication.

        Returns:
            Base64 encoded QR image, or None on error
        """
        try:
            response = self._make_request(
                "GET", f"/api/{self.session_name}/auth/qr", timeout=10
            )
            # WAHA returns {"value": "base64_qr_data"}
            return response.get("value")
        except Exception as e:
            logger.error(f"Failed to get QR code: {e}")
            return None

    def check_connection(self) -> Dict[str, Any]:
        """Check session connection status."""
        try:
            response = self._make_request("GET", f"/api/sessions/{self.session_name}")
            return {
                "status": response.get("status"),
                "name": response.get("name"),
                "me": response.get("me"),  # Connected phone info
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def send_message(self, message: WhatsAppMessage) -> WhatsAppResponse:
        """Send text message via WAHA."""
        try:
            # Format phone number for WhatsApp (add @c.us suffix)
            chat_id = self._format_chat_id(message.to)

            response = self._make_request(
                "POST",
                "/api/sendText",
                {
                    "session": self.session_name,
                    "chatId": chat_id,
                    "text": message.text,
                },
            )

            return WhatsAppResponse(
                success=True,
                message_id=response.get("id"),
                raw_response=response,
            )

        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return WhatsAppResponse(success=False, error=str(e))

    def send_photo(
        self,
        to: str,
        photo_url: str,
        caption: Optional[str] = None,
    ) -> WhatsAppResponse:
        """Send photo via WAHA."""
        try:
            chat_id = self._format_chat_id(to)

            response = self._make_request(
                "POST",
                "/api/sendImage",
                {
                    "session": self.session_name,
                    "chatId": chat_id,
                    "file": {"url": photo_url},
                    "caption": caption or "",
                },
            )

            return WhatsAppResponse(
                success=True,
                message_id=response.get("id"),
                raw_response=response,
            )

        except Exception as e:
            logger.error(f"Failed to send photo: {e}")
            return WhatsAppResponse(success=False, error=str(e))

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify HMAC-SHA512 signature from WAHA webhook.

        Args:
            payload: Raw request body bytes
            signature: X-Webhook-Hmac-Sha512 header value

        Returns:
            True if signature is valid
        """
        if not self.webhook_secret:
            logger.warning("WAHA webhook secret not configured")
            return True  # Skip verification if no secret

        expected = hmac.new(
            self.webhook_secret.encode(),
            payload,
            hashlib.sha512,
        ).hexdigest()

        return hmac.compare_digest(expected, signature)

    def process_webhook(self, data: Dict) -> Optional[WhatsAppIncomingMessage]:
        """Process incoming WAHA webhook.

        Args:
            data: Webhook payload from WAHA

        Returns:
            Parsed message or None for non-message events
        """
        event = data.get("event")
        session = data.get("session")
        payload = data.get("payload", {})

        if event == "message":
            # Extract sender number (remove @c.us suffix)
            from_number = payload.get("from", "").replace("@c.us", "")

            # Skip messages from ourselves
            if payload.get("fromMe"):
                return None

            return WhatsAppIncomingMessage(
                message_type="message",
                from_number=from_number,
                text=payload.get("body", ""),
                message_id=payload.get("id", ""),
                has_media=payload.get("hasMedia", False),
                timestamp=payload.get("timestamp"),
                session_name=session,
            )

        elif event == "session.status":
            # Return status update as special message type
            status = payload.get("status")
            return WhatsAppIncomingMessage(
                message_type="status",
                from_number="",
                text=status,
                message_id="",
                session_name=session,
            )

        return None

    def _format_chat_id(self, phone: str) -> str:
        """Format phone number to WhatsApp chat ID.

        Args:
            phone: Phone number (e.g., 79001234567 or +79001234567)

        Returns:
            Chat ID with @c.us suffix
        """
        # Remove + and spaces
        clean = phone.replace("+", "").replace(" ", "").replace("-", "")
        return f"{clean}@c.us"

    def _update_bot_error(self, error: str):
        """Update bot's last_error field."""
        self.bot.last_error = error
        self.bot.save(update_fields=["last_error"])
