"""Lightweight WAHA client for OTP service.

Not tied to WhatsAppBot model — uses session_name directly from settings.
Only implements methods needed for OTP: send_text, session management, QR.
"""

import base64
import logging
from typing import Dict, Optional

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class WAHAOTPError(Exception):
    """WAHA OTP client error."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class WAHAOTPClient:
    """Simplified WAHA client for OTP bot operations."""

    def __init__(self, session_name: Optional[str] = None) -> None:
        self.base_url: str = getattr(settings, "WAHA_BASE_URL", "http://waha:3000")
        self.api_key: str = getattr(settings, "WAHA_API_KEY", "")
        self.session_name: str = session_name or getattr(
            settings, "WAHA_OTP_SESSION_NAME", "default"
        )

    def _headers(self) -> Dict[str, str]:
        return {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json",
        }

    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make HTTP request to WAHA API."""
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self._headers(),
                json=data,
                timeout=30,
            )
            if response.status_code >= 400:
                error_text = response.text[:200]
                logger.error(f"[WAHA_OTP] {method} {endpoint}: {response.status_code} {error_text}")
                raise WAHAOTPError(error_text, status_code=response.status_code)
            return response.json() if response.text else {}
        except requests.exceptions.RequestException as e:
            logger.error(f"[WAHA_OTP] Connection error: {e}")
            raise WAHAOTPError(f"WAHA connection error: {str(e)}")

    def start_session(self) -> bool:
        """Start/create the OTP WAHA session with webhook for incoming messages."""
        logger.info(f"[WAHA_OTP] Starting session: {self.session_name}")

        # Get backend URL for webhook callback
        backend_url = getattr(settings, "BACKEND_URL", "https://api.appofiz.com")

        try:
            self._request("POST", "/api/sessions/start", {
                "name": self.session_name,
                "config": {
                    "webhooks": [
                        {
                            "url": f"{backend_url}/api/v1/otp-bot/webhook/",
                            "events": ["message"],
                        }
                    ],
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
            response = requests.get(url, headers=self._headers(), timeout=15)
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
        except requests.exceptions.RequestException as e:
            logger.error(f"[WAHA_OTP] QR connection error: {e}")
            return None

    def get_me(self) -> Optional[Dict]:
        """Get connected phone info."""
        try:
            return self._request("GET", f"/api/sessions/{self.session_name}/me")
        except WAHAOTPError:
            return None

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
            response = requests.get(
                url,
                headers=self._headers(),
                timeout=30,
            )

            if response.status_code >= 400:
                logger.error(f"[WAHA_OTP] Download error: {response.status_code}")
                return None

            logger.info(f"[WAHA_OTP] Downloaded {len(response.content)} bytes")
            return response.content

        except requests.exceptions.RequestException as e:
            logger.error(f"[WAHA_OTP] Download error: {e}")
            return None
