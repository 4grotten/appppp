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
from .http_client import waha_request

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
        # WAHA Plus: Multi-session support enabled
        # Each organization gets its own session: org_{organization_id}
        # Falls back to "default" for OTP bot or if not configured
        if whatsapp_bot.waha_session_name:
            self.session_name = whatsapp_bot.waha_session_name
        elif whatsapp_bot.organization_id:
            self.session_name = f"org_{whatsapp_bot.organization_id}"
        else:
            self.session_name = "default"

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        timeout: tuple = None,
    ) -> Dict:
        """Make HTTP request to WAHA API using shared connection pool.

        Uses waha_request() which provides:
        - Connection pooling
        - Automatic retries on 429/502/503/504
        - Pre-configured headers (API key, Content-Type)
        - Default timeout

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., /api/sessions)
            data: Request body for POST/PUT
            timeout: Optional (connect, read) timeout tuple

        Returns:
            Response JSON as dict

        Raises:
            requests.exceptions.RequestException: On network errors
        """
        url = f"{self.base_url}{endpoint}"
        try:
            response = waha_request(
                method=method,
                url=url,
                json=data,
                timeout=timeout,
            )
            response.raise_for_status()
            return response.json() if response.text else {}
        except requests.exceptions.Timeout:
            logger.error(f"[WAHA] Request timeout: {method} {endpoint}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"[WAHA] Request error: {method} {endpoint} - {e}")
            raise

    def is_healthy(self) -> bool:
        """Check if WAHA service is available.

        Uses /api/sessions endpoint which always exists in WAHA.
        """
        try:
            self._make_request("GET", "/api/sessions", timeout=(3, 5))
            return True
        except Exception:
            return False

    def start_session(self) -> bool:
        """Create and start WAHA session.

        Uses POST /api/sessions/start which does "upsert and start":
        - Creates session if it doesn't exist
        - Starts session if it exists but stopped
        - Does nothing if already running
        """
        try:
            backend_url = getattr(settings, "BACKEND_URL", "https://api.appofiz.com")

            # Upsert and Start session (creates if not exists, starts if exists)
            self._make_request(
                "POST",
                "/api/sessions/start",
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

            logger.info(f"WAHA session started: {self.session_name}")
            return True

        except requests.exceptions.HTTPError as e:
            error_msg = str(e)
            try:
                error_data = e.response.json()
                error_msg = error_data.get("message", str(e))
            except Exception:
                pass
            logger.error(f"Failed to start WAHA session: {error_msg}")
            self._update_bot_error(error_msg)
            return False

        except Exception as e:
            logger.error(f"Failed to start WAHA session: {e}")
            self._update_bot_error(str(e))
            return False

    def stop_session(self) -> bool:
        """Stop WAHA session (keeps session data, can restart)."""
        try:
            self._make_request("POST", f"/api/sessions/{self.session_name}/stop")
            logger.info(f"WAHA session stopped: {self.session_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to stop WAHA session: {e}")
            return False

    def logout_session(self) -> bool:
        """Logout from WhatsApp (requires QR re-scan to reconnect)."""
        try:
            self._make_request(
                "POST",
                "/api/sessions/logout",
                {"name": self.session_name},
            )
            logger.info(f"WAHA session logged out: {self.session_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to logout WAHA session: {e}")
            return False

    def delete_session(self) -> bool:
        """Delete session completely (removes all session data from WAHA)."""
        try:
            self._make_request("DELETE", f"/api/sessions/{self.session_name}")
            logger.info(f"WAHA session deleted: {self.session_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete WAHA session: {e}")
            return False

    def get_qr_code(self) -> Optional[str]:
        """Get QR code for WhatsApp authentication.

        Returns:
            Base64 encoded QR image, or None on error
        """
        try:
            response = self._make_request(
                "GET", f"/api/{self.session_name}/auth/qr", timeout=(5, 10)
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

    def send_typing(self, to: str, duration: int = 3000) -> bool:
        """Send typing indicator via WAHA.

        Shows "typing..." status to the user for specified duration.

        Args:
            to: Phone number to show typing to
            duration: Duration in milliseconds (default 3000ms = 3 seconds)

        Returns:
            True if successful
        """
        try:
            chat_id = self._format_chat_id(to)

            self._make_request(
                "POST",
                "/api/startTyping",
                {
                    "session": self.session_name,
                    "chatId": chat_id,
                    "duration": duration,
                },
                timeout=(3, 5),
            )
            logger.debug(f"WAHA: Typing indicator sent to {chat_id}")
            return True

        except Exception as e:
            # Non-critical error, just log and continue
            logger.debug(f"WAHA: Failed to send typing indicator: {e}")
            return False

    def stop_typing(self, to: str) -> bool:
        """Stop typing indicator via WAHA.

        Args:
            to: Phone number to stop typing for

        Returns:
            True if successful
        """
        try:
            chat_id = self._format_chat_id(to)

            self._make_request(
                "POST",
                "/api/stopTyping",
                {
                    "session": self.session_name,
                    "chatId": chat_id,
                },
                timeout=(3, 5),
            )
            return True

        except Exception as e:
            logger.debug(f"WAHA: Failed to stop typing indicator: {e}")
            return False

    def mark_as_read(self, to: str, message_id: Optional[str] = None) -> bool:
        """Mark messages as read (send seen status) via WAHA.

        Shows blue checkmarks to the sender.

        Args:
            to: Phone number/chat ID
            message_id: Optional specific message ID to mark as read

        Returns:
            True if successful
        """
        try:
            chat_id = self._format_chat_id(to)

            self._make_request(
                "POST",
                "/api/sendSeen",
                {
                    "session": self.session_name,
                    "chatId": chat_id,
                },
                timeout=(3, 5),
            )
            logger.debug(f"WAHA: Marked messages as read for {chat_id}")
            return True

        except Exception as e:
            # Non-critical error, just log and continue
            logger.debug(f"WAHA: Failed to mark as read: {e}")
            return False

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

    def get_profile_picture(self, phone: str) -> Optional[str]:
        """Get contact's profile picture URL.

        Args:
            phone: Phone number (e.g., 79001234567)

        Returns:
            Profile picture URL or None if not available
        """
        try:
            chat_id = self._format_chat_id(phone)
            response = self._make_request(
                "GET",
                f"/api/contacts/profile-picture?contactId={chat_id}&session={self.session_name}",
                timeout=(5, 10),
            )
            # WAHA returns {"profilePictureURL": "https://..."}
            return response.get("profilePictureURL")
        except Exception as e:
            logger.debug(f"Failed to get profile picture for {phone}: {e}")
            return None

    def _update_bot_error(self, error: str):
        """Update bot's last_error field."""
        self.bot.last_error = error
        self.bot.save(update_fields=["last_error"])

    # ============================================================
    # WAHA Plus Features - Interactive Messages
    # ============================================================

    def send_buttons(
        self,
        to: str,
        text: str,
        buttons: list,
        header: Optional[str] = None,
        footer: Optional[str] = None,
    ) -> WhatsAppResponse:
        """Send message with reply buttons (WAHA Plus).

        Args:
            to: Phone number
            text: Message body text
            buttons: List of button dicts [{"id": "btn_1", "text": "Button 1"}, ...]
            header: Optional header text
            footer: Optional footer text

        Returns:
            WhatsAppResponse with message_id
        """
        try:
            chat_id = self._format_chat_id(to)

            # Format buttons for WAHA API (max 3 buttons)
            formatted_buttons = [
                {"id": btn.get("id", f"btn_{i}"), "text": btn.get("text", btn.get("title", ""))}
                for i, btn in enumerate(buttons[:3])
            ]

            payload = {
                "session": self.session_name,
                "chatId": chat_id,
                "body": text,
                "buttons": formatted_buttons,
            }

            if header:
                payload["header"] = header
            if footer:
                payload["footer"] = footer

            response = self._make_request("POST", "/api/sendButtons", payload)

            return WhatsAppResponse(
                success=True,
                message_id=response.get("id"),
                raw_response=response,
            )

        except Exception as e:
            logger.error(f"Failed to send buttons: {e}")
            # Fallback to plain text with numbered options
            fallback_text = f"{text}\n\n"
            for i, btn in enumerate(buttons[:3], 1):
                fallback_text += f"{i}. {btn.get('text', btn.get('title', ''))}\n"
            return self.send_message(WhatsAppMessage(to=to, text=fallback_text.strip()))

    def send_list(
        self,
        to: str,
        text: str,
        button_text: str,
        sections: list,
        header: Optional[str] = None,
        footer: Optional[str] = None,
    ) -> WhatsAppResponse:
        """Send list/menu message (WAHA Plus).

        Args:
            to: Phone number
            text: Message body text
            button_text: Text on the button that opens the list
            sections: List of sections with rows:
                [{"title": "Section 1", "rows": [{"id": "row_1", "title": "Item 1", "description": "..."}]}]
            header: Optional header text
            footer: Optional footer text

        Returns:
            WhatsAppResponse with message_id
        """
        try:
            chat_id = self._format_chat_id(to)

            payload = {
                "session": self.session_name,
                "chatId": chat_id,
                "body": text,
                "buttonText": button_text,
                "sections": sections,
            }

            if header:
                payload["header"] = header
            if footer:
                payload["footer"] = footer

            response = self._make_request("POST", "/api/sendList", payload)

            return WhatsAppResponse(
                success=True,
                message_id=response.get("id"),
                raw_response=response,
            )

        except Exception as e:
            logger.error(f"Failed to send list: {e}")
            # Fallback to plain text
            fallback_text = f"{text}\n\n"
            for section in sections:
                if section.get("title"):
                    fallback_text += f"*{section['title']}*\n"
                for row in section.get("rows", []):
                    fallback_text += f"• {row.get('title', '')}\n"
            return self.send_message(WhatsAppMessage(to=to, text=fallback_text.strip()))

    def send_contacts_button(
        self,
        to: str,
        text: str,
        contacts: list,
    ) -> WhatsAppResponse:
        """Send message with contact card button.

        Convenience method to send organization contacts via interactive button.

        Args:
            to: Phone number
            text: Intro text
            contacts: List of contact dicts with name, phone, email, etc.

        Returns:
            WhatsAppResponse with message_id
        """
        buttons = [
            {"id": "view_contacts", "text": "📞 Контакты"},
        ]

        if len(contacts) > 0:
            # Build contact info text
            contact_text = f"{text}\n\n"
            for contact in contacts[:5]:  # Max 5 contacts
                name = contact.get("name", "")
                phone = contact.get("phone", "")
                email = contact.get("email", "")

                if name:
                    contact_text += f"👤 *{name}*\n"
                if phone:
                    contact_text += f"📱 {phone}\n"
                if email:
                    contact_text += f"📧 {email}\n"
                contact_text += "\n"

            return self.send_message(WhatsAppMessage(to=to, text=contact_text.strip()))

        return self.send_buttons(to=to, text=text, buttons=buttons)

    def send_reaction(
        self,
        to: str,
        message_id: str,
        emoji: str,
    ) -> WhatsAppResponse:
        """Send reaction to a message (WAHA Plus).

        Args:
            to: Phone number (chat ID)
            message_id: ID of the message to react to
            emoji: Emoji to react with (e.g., "👍", "❤️", "😂")

        Returns:
            WhatsAppResponse
        """
        try:
            chat_id = self._format_chat_id(to)

            response = self._make_request(
                "POST",
                "/api/reaction",
                {
                    "session": self.session_name,
                    "chatId": chat_id,
                    "messageId": message_id,
                    "reaction": emoji,
                },
            )

            return WhatsAppResponse(
                success=True,
                message_id=response.get("id"),
                raw_response=response,
            )

        except Exception as e:
            logger.error(f"Failed to send reaction: {e}")
            return WhatsAppResponse(success=False, error=str(e))

    def send_poll(
        self,
        to: str,
        name: str,
        options: list,
        multiple_answers: bool = False,
    ) -> WhatsAppResponse:
        """Send poll message (WAHA Plus).

        Args:
            to: Phone number
            name: Poll question/title
            options: List of option strings ["Option 1", "Option 2", ...]
            multiple_answers: Allow multiple selections

        Returns:
            WhatsAppResponse with message_id
        """
        try:
            chat_id = self._format_chat_id(to)

            response = self._make_request(
                "POST",
                "/api/sendPoll",
                {
                    "session": self.session_name,
                    "chatId": chat_id,
                    "name": name,
                    "options": options[:12],  # WhatsApp max 12 options
                    "multipleAnswers": multiple_answers,
                },
            )

            return WhatsAppResponse(
                success=True,
                message_id=response.get("id"),
                raw_response=response,
            )

        except Exception as e:
            logger.error(f"Failed to send poll: {e}")
            return WhatsAppResponse(success=False, error=str(e))

    def send_location(
        self,
        to: str,
        latitude: float,
        longitude: float,
        name: Optional[str] = None,
        address: Optional[str] = None,
    ) -> WhatsAppResponse:
        """Send location message.

        Args:
            to: Phone number
            latitude: Location latitude
            longitude: Location longitude
            name: Optional location name
            address: Optional location address

        Returns:
            WhatsAppResponse with message_id
        """
        try:
            chat_id = self._format_chat_id(to)

            payload = {
                "session": self.session_name,
                "chatId": chat_id,
                "latitude": latitude,
                "longitude": longitude,
            }

            if name:
                payload["name"] = name
            if address:
                payload["address"] = address

            response = self._make_request("POST", "/api/sendLocation", payload)

            return WhatsAppResponse(
                success=True,
                message_id=response.get("id"),
                raw_response=response,
            )

        except Exception as e:
            logger.error(f"Failed to send location: {e}")
            return WhatsAppResponse(success=False, error=str(e))
