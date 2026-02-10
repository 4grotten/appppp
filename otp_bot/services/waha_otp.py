"""Lightweight WAHA client for OTP service.

Not tied to WhatsAppBot model — uses session_name directly from settings.
Only implements methods needed for OTP: send_text, session management, QR.

Uses shared HTTP client with:
- Connection pooling
- Automatic retries on 429/502/503/504
- Default timeout
"""

import base64
import logging
from typing import Dict, Optional

from django.conf import settings

from messenger_bots.services.whatsapp.http_client import waha_request
from otp_bot.metrics import track_timing

logger = logging.getLogger(__name__)


class WAHAOTPError(Exception):
    """WAHA OTP client error."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class WAHAOTPClient:
    """Simplified WAHA client for OTP bot operations.

    Uses shared HTTP session from messenger_bots for connection pooling
    and automatic retries.
    """

    def __init__(self, session_name: Optional[str] = None) -> None:
        self.base_url: str = getattr(settings, "WAHA_BASE_URL", "http://waha:3000")
        self.session_name: str = session_name or getattr(
            settings, "WAHA_OTP_SESSION_NAME", "default"
        )

    def _request(
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
        - Pre-configured headers
        - Default timeout

        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request body
            timeout: Optional (connect, read) timeout tuple

        Returns:
            Response JSON as dict

        Raises:
            WAHAOTPError: On HTTP errors or connection failures
        """
        url = f"{self.base_url}{endpoint}"
        try:
            response = waha_request(
                method=method,
                url=url,
                json=data,
                timeout=timeout,
            )
            if response.status_code >= 400:
                error_text = response.text[:200]
                logger.error(f"[WAHA_OTP] {method} {endpoint}: {response.status_code} {error_text}")
                raise WAHAOTPError(error_text, status_code=response.status_code)
            return response.json() if response.text else {}
        except WAHAOTPError:
            raise
        except Exception as e:
            logger.error(f"[WAHA_OTP] Connection error: {e}")
            raise WAHAOTPError(f"WAHA connection error: {str(e)}")

    def start_session(self) -> bool:
        """Start/create the OTP WAHA session with webhook for incoming messages."""
        logger.info(f"[WAHA_OTP] Starting session: {self.session_name}")

        # Get backend URL for webhook callback
        backend_url = getattr(settings, "BACKEND_URL", "https://api.appofiz.com")

        try:
            # Note: Don't add otp-bot webhook here - we route from messenger_bots webhook
            # to avoid duplicate message processing
            self._request("POST", "/api/sessions/start", {
                "name": self.session_name,
                "config": {
                    "noweb": {
                        "store": {
                            "enabled": True,
                            "full_sync": True,
                        }
                    },
                },
            })
            logger.info(f"[WAHA_OTP] Session started with webhook: {backend_url}/api/v1/otp-bot/webhook/")
            return True
        except WAHAOTPError as e:
            logger.error(f"[WAHA_OTP] Failed to start session: {e.message}")
            return False

    def stop_session(self) -> bool:
        """Stop the OTP WAHA session."""
        logger.info(f"[WAHA_OTP] Stopping session: {self.session_name}")
        try:
            self._request("POST", "/api/sessions/stop", {
                "name": self.session_name,
            })
            return True
        except WAHAOTPError:
            return False

    def logout_session(self) -> bool:
        """Logout from WhatsApp (requires QR re-scan to reconnect)."""
        logger.info(f"[WAHA_OTP] Logging out session: {self.session_name}")
        try:
            self._request("POST", "/api/sessions/logout", {
                "name": self.session_name,
            })
            return True
        except WAHAOTPError:
            return False

    def delete_session(self) -> bool:
        """Delete session completely (removes all session data)."""
        logger.info(f"[WAHA_OTP] Deleting session: {self.session_name}")
        try:
            self._request("DELETE", f"/api/sessions/{self.session_name}")
            return True
        except WAHAOTPError:
            return False

    def get_session_status(self) -> str:
        """Get session status string (WORKING, SCAN_QR, STOPPED, etc.)."""
        try:
            result = self._request("GET", f"/api/sessions/{self.session_name}")
            return result.get("status", "STOPPED").upper()
        except WAHAOTPError:
            return "STOPPED"

    def get_qr_code(self) -> Optional[str]:
        """Get QR code for authentication as base64 PNG string."""
        url = f"{self.base_url}/api/{self.session_name}/auth/qr"
        try:
            response = waha_request("GET", url, timeout=(5, 15))
            if response.status_code >= 400:
                logger.error(f"[WAHA_OTP] QR request failed: {response.status_code}")
                return None

            content_type = response.headers.get("Content-Type", "")

            # WAHA returns QR as PNG image
            if "image" in content_type:
                return base64.b64encode(response.content).decode("utf-8")

            # Fallback: try JSON response
            try:
                data = response.json()
                return data.get("data") or data.get("value")
            except ValueError:
                # If not JSON and not image, try to encode raw bytes
                if response.content:
                    return base64.b64encode(response.content).decode("utf-8")
                return None
        except Exception as e:
            logger.error(f"[WAHA_OTP] QR connection error: {e}")
            return None

    def get_me(self) -> Optional[Dict]:
        """Get connected phone info."""
        try:
            return self._request("GET", f"/api/sessions/{self.session_name}/me")
        except WAHAOTPError:
            return None

    @track_timing("waha_send_text")
    def send_text(self, phone_number: str, text: str) -> bool:
        """Send a text message via WhatsApp.

        Args:
            phone_number: E.164 format (e.g., +79991234567)
            text: Message body

        Returns:
            True if sent successfully
        """
        chat_id = phone_number.lstrip("+") + "@c.us"
        masked_phone = phone_number[:7] + "***"
        logger.info(f"[WAHA_OTP] Sending message to {masked_phone}")

        try:
            self._request("POST", "/api/sendText", {
                "session": self.session_name,
                "chatId": chat_id,
                "text": text,
            })
            logger.info(f"[WAHA_OTP] Message sent to {masked_phone}")
            return True
        except WAHAOTPError as e:
            logger.error(f"[WAHA_OTP] Failed to send to {masked_phone}: {e.message}")
            return False

    def is_healthy(self) -> bool:
        """Check if session is healthy and ready to send."""
        status = self.get_session_status()
        return status in ("WORKING", "AUTHENTICATED")

    def send_voice(self, phone_number: str, audio_url: str) -> bool:
        """Send voice message via WhatsApp using audio URL.

        Args:
            phone_number: E.164 format (e.g., +79991234567)
            audio_url: URL to audio file (MP3/OGG)

        Returns:
            True if sent successfully
        """
        chat_id = phone_number.lstrip("+") + "@c.us"
        masked_phone = phone_number[:7] + "***"
        logger.info(f"[WAHA_OTP] Sending voice to {masked_phone}")

        try:
            self._request("POST", "/api/sendVoice", {
                "session": self.session_name,
                "chatId": chat_id,
                "file": {"url": audio_url},
                "convert": True,  # Auto-convert MP3 to OPUS/OGG
            })
            logger.info(f"[WAHA_OTP] Voice sent to {masked_phone}")
            return True
        except WAHAOTPError as e:
            logger.error(f"[WAHA_OTP] Failed to send voice to {masked_phone}: {e.message}")
            return False

    @track_timing("waha_send_voice")
    def send_voice_base64(
        self, phone_number: str, audio_bytes: bytes, mimetype: str = "audio/mpeg"
    ) -> bool:
        """Send voice message via WhatsApp using base64 encoded audio.

        Args:
            phone_number: E.164 format
            audio_bytes: Raw audio bytes
            mimetype: Audio MIME type (audio/mpeg for MP3)

        Returns:
            True if sent successfully
        """
        chat_id = phone_number.lstrip("+") + "@c.us"
        masked_phone = phone_number[:7] + "***"
        logger.info(f"[WAHA_OTP] Sending voice (base64) to {masked_phone}, size={len(audio_bytes)} bytes")

        # Encode to base64
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

        try:
            self._request("POST", "/api/sendVoice", {
                "session": self.session_name,
                "chatId": chat_id,
                "file": {
                    "data": audio_b64,
                    "mimetype": mimetype,
                },
                "convert": True,
            })
            logger.info(f"[WAHA_OTP] Voice (base64) sent to {masked_phone}")
            return True
        except WAHAOTPError as e:
            logger.error(f"[WAHA_OTP] Failed to send voice: {e.message}")
            return False

    def download_media(self, message_id: str) -> Optional[bytes]:
        """Download media file from a WhatsApp message.

        Args:
            message_id: Message ID containing media

        Returns:
            Raw media bytes or None on error
        """
        logger.info(f"[WAHA_OTP] Downloading media: {message_id[:30]}...")

        try:
            url = f"{self.base_url}/api/{self.session_name}/messages/{message_id}/download"
            response = waha_request("GET", url, timeout=(5, 30))

            if response.status_code >= 400:
                logger.error(f"[WAHA_OTP] Download error: {response.status_code}")
                return None

            logger.info(f"[WAHA_OTP] Downloaded {len(response.content)} bytes")
            return response.content

        except Exception as e:
            logger.error(f"[WAHA_OTP] Download error: {e}")
            return None

    def send_buttons(
        self,
        phone_number: str,
        text: str,
        buttons: list,
        footer: Optional[str] = None,
    ) -> bool:
        """Send interactive button message via WhatsApp.

        WAHA NOWEB format for buttons.
        Buttons appear as clickable options below the message.

        Args:
            phone_number: E.164 format (e.g., +79991234567)
            text: Message body text
            buttons: List of button dicts [{"id": "btn1", "text": "Button Text"}, ...]
                     Maximum 3 buttons allowed by WhatsApp
            footer: Optional footer text displayed below buttons

        Returns:
            True if sent successfully
        """
        chat_id = phone_number.lstrip("+") + "@c.us"
        masked_phone = phone_number[:7] + "***"
        logger.info(f"[WAHA_OTP] Sending buttons to {masked_phone}")

        # WhatsApp allows max 3 buttons
        buttons_limited = buttons[:3]

        payload = {
            "session": self.session_name,
            "chatId": chat_id,
            "title": "",  # Optional header
            "body": text,
            "footer": footer or "",
            "buttons": [
                {"id": btn.get("id", f"btn_{i}"), "text": btn.get("text", "")}
                for i, btn in enumerate(buttons_limited)
            ],
        }

        try:
            self._request("POST", "/api/sendButtons", payload)
            logger.info(f"[WAHA_OTP] Buttons sent to {masked_phone}")
            return True
        except WAHAOTPError as e:
            logger.error(f"[WAHA_OTP] Failed to send buttons to {masked_phone}: {e.message}")
            return False

    def send_list(
        self,
        phone_number: str,
        text: str,
        button_text: str,
        sections: list,
        title: Optional[str] = None,
        footer: Optional[str] = None,
    ) -> bool:
        """Send interactive list message via WhatsApp.

        List messages show a button that opens a menu with multiple options
        organized in sections.

        Args:
            phone_number: E.164 format (e.g., +79991234567)
            text: Message body text
            button_text: Text on the button that opens the list menu
            sections: List of section dicts:
                [{"title": "Section 1", "rows": [{"id": "1", "title": "Option 1", "description": "..."}]}]
            title: Optional header title
            footer: Optional footer text

        Returns:
            True if sent successfully
        """
        chat_id = phone_number.lstrip("+") + "@c.us"
        masked_phone = phone_number[:7] + "***"
        logger.info(f"[WAHA_OTP] Sending list to {masked_phone}")

        payload = {
            "session": self.session_name,
            "chatId": chat_id,
            "title": title or "",
            "body": text,
            "footer": footer or "",
            "buttonText": button_text,
            "sections": sections,
        }

        try:
            self._request("POST", "/api/sendList", payload)
            logger.info(f"[WAHA_OTP] List sent to {masked_phone}")
            return True
        except WAHAOTPError as e:
            logger.error(f"[WAHA_OTP] Failed to send list to {masked_phone}: {e.message}")
            return False

    def send_interactive_buttons(
        self,
        phone_number: str,
        text: str,
        buttons: list,
        header: Optional[str] = None,
        footer: Optional[str] = None,
    ) -> bool:
        """Send interactive message with URL/Call/Reply buttons (WAHA Plus).

        Supports mixed button types:
        - URL: Opens link in browser
        - Call: Initiates phone call
        - Reply: Quick reply with callback
        - Copy: Copy text to clipboard

        Args:
            phone_number: E.164 format (e.g., +79991234567)
            text: Message body text
            buttons: List of button dicts:
                - URL: {"type": "url", "text": "Open", "url": "https://..."}
                - Call: {"type": "call", "text": "Call", "phone": "+79001234567"}
                - Reply: {"type": "reply", "id": "btn_id", "text": "Click"}
                - Copy: {"type": "copy", "text": "Copy", "copy_text": "PROMO123"}
            header: Optional header text
            footer: Optional footer text

        Returns:
            True if sent successfully
        """
        chat_id = phone_number.lstrip("+") + "@c.us"
        masked_phone = phone_number[:7] + "***"
        logger.info(f"[WAHA_OTP] Sending interactive buttons to {masked_phone}")

        # Build buttons payload for WAHA Plus format
        formatted_buttons = []
        for i, btn in enumerate(buttons[:3]):  # Max 3 buttons
            btn_type = btn.get("type", "reply")

            if btn_type == "url":
                formatted_buttons.append({
                    "type": "url",
                    "text": btn.get("text", "Open"),
                    "url": btn.get("url", ""),
                })
            elif btn_type == "call":
                formatted_buttons.append({
                    "type": "call",
                    "text": btn.get("text", "Call"),
                    "phone": btn.get("phone", ""),
                })
            elif btn_type == "copy":
                formatted_buttons.append({
                    "type": "copy",
                    "text": btn.get("text", "Copy"),
                    "copyCode": btn.get("copy_text", ""),
                })
            else:  # reply
                formatted_buttons.append({
                    "type": "reply",
                    "id": btn.get("id", f"btn_{i}"),
                    "text": btn.get("text", ""),
                })

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

        try:
            # WAHA Plus endpoint for interactive messages
            self._request("POST", "/api/sendInteractiveMessage", payload)
            logger.info(f"[WAHA_OTP] Interactive buttons sent to {masked_phone}")
            return True
        except WAHAOTPError as e:
            logger.warning(f"[WAHA_OTP] Interactive buttons failed: {e.message}, trying reply buttons")
            # Fallback to reply buttons for WAHA Core or old clients
            return self._fallback_to_reply_buttons(phone_number, text, buttons, footer)

    def _fallback_to_reply_buttons(
        self,
        phone_number: str,
        text: str,
        buttons: list,
        footer: Optional[str] = None,
    ) -> bool:
        """Fallback to simple reply buttons when interactive buttons fail."""
        # Convert all buttons to reply type
        reply_buttons = []
        for i, btn in enumerate(buttons[:3]):
            reply_buttons.append({
                "id": btn.get("id", f"btn_{i}"),
                "text": btn.get("text", "Button"),
            })

        return self.send_buttons(phone_number, text, reply_buttons, footer)

    def send_menu(
        self,
        phone_number: str,
        welcome_text: Optional[str] = None,
    ) -> bool:
        """Send main menu with interactive buttons.

        Displays the bot's main menu with options:
        - Voice Assistant (URL to EasyCard Voice AI)
        - Get Card (URL to cards page)
        - Reply button for chat

        Configure via Django settings:
        - OTP_BOT_VOICE_ASSISTANT_URL: Voice assistant URL
        - OTP_BOT_CARDS_URL: Cards page URL

        Args:
            phone_number: E.164 format
            welcome_text: Optional custom welcome text

        Returns:
            True if sent successfully
        """
        # Get URLs from settings
        voice_url = getattr(
            settings,
            "OTP_BOT_VOICE_ASSISTANT_URL",
            "https://easycarduae.com/voice-assistant"
        )
        cards_url = getattr(settings, "OTP_BOT_CARDS_URL", "https://easycarduae.com/cards")

        text = welcome_text or (
            "👋 Привет! Я ваш ассистент EasyCard.\n\n"
            "Выберите действие или напишите ваш вопрос:"
        )

        buttons = [
            {
                "type": "url",
                "text": "🎙 Голосовой ассистент",
                "url": voice_url,
            },
            {
                "type": "url",
                "text": "💳 Получить карту",
                "url": cards_url,
            },
            {
                "type": "reply",
                "id": "start_chat",
                "text": "💬 Начать чат",
            },
        ]

        return self.send_interactive_buttons(
            phone_number=phone_number,
            text=text,
            buttons=buttons,
            footer="EasyCard UAE",
        )
