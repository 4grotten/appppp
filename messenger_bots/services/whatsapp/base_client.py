"""Base WAHA client with shared functionality.

Provides common HTTP request handling used by both:
- WAHAService (messenger_bots for organizations)
- WAHAOTPClient (OTP bot)
"""

import logging
from typing import Any, Dict, Optional

from django.conf import settings

from .http_client import waha_request

logger = logging.getLogger(__name__)


class WAHAError(Exception):
    """Base WAHA client error."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class BaseWAHAClient:
    """Base class for WAHA clients with shared HTTP handling.

    Provides:
    - Common request method using shared connection pool
    - Session management (start, stop, logout, delete)
    - Health check
    - Chat ID formatting

    Subclasses should set:
    - self.base_url
    - self.session_name
    """

    def __init__(self):
        self.base_url: str = getattr(settings, "WAHA_BASE_URL", "http://waha:3000")
        self.session_name: str = "default"

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        timeout: tuple = None,
        raise_on_error: bool = True,
    ) -> Dict[str, Any]:
        """Make HTTP request to WAHA API using shared connection pool.

        Uses waha_request() which provides:
        - Connection pooling (50 connections)
        - Automatic retries on 429/502/503/504
        - Exponential backoff with jitter
        - Default timeout (5s connect, 30s read)

        Args:
            method: HTTP method (GET, POST, DELETE)
            endpoint: API endpoint (e.g., /api/sessions)
            data: Request body for POST/PUT
            timeout: Optional (connect, read) timeout tuple
            raise_on_error: If True, raise WAHAError on 4xx/5xx responses

        Returns:
            Response JSON as dict

        Raises:
            WAHAError: On HTTP errors (if raise_on_error=True) or connection failures
        """
        url = f"{self.base_url}{endpoint}"
        log_prefix = self._get_log_prefix()

        try:
            response = waha_request(
                method=method,
                url=url,
                json=data,
                timeout=timeout,
            )

            if response.status_code >= 400:
                error_text = response.text[:200]
                logger.error(f"{log_prefix} {method} {endpoint}: {response.status_code} {error_text}")
                if raise_on_error:
                    raise WAHAError(error_text, status_code=response.status_code)
                return {"error": error_text, "status_code": response.status_code}

            return response.json() if response.text else {}

        except WAHAError:
            raise
        except Exception as e:
            logger.error(f"{log_prefix} Connection error: {method} {endpoint} - {e}")
            raise WAHAError(f"Connection error: {str(e)}")

    def _get_log_prefix(self) -> str:
        """Get log prefix for this client. Override in subclasses."""
        return "[WAHA]"

    def is_healthy(self) -> bool:
        """Check if WAHA service is available."""
        try:
            self._request("GET", "/api/sessions", timeout=(3, 5))
            return True
        except WAHAError:
            return False

    def get_session_status(self) -> str:
        """Get session status string (WORKING, SCAN_QR, STOPPED, etc.)."""
        try:
            result = self._request(
                "GET",
                f"/api/sessions/{self.session_name}",
                raise_on_error=False,
            )
            if "error" in result:
                return "STOPPED"
            return result.get("status", "STOPPED").upper()
        except WAHAError:
            return "STOPPED"

    def start_session(self, config: Optional[Dict] = None) -> bool:
        """Start/create WAHA session.

        Args:
            config: Optional session configuration

        Returns:
            True if started successfully
        """
        log_prefix = self._get_log_prefix()
        logger.info(f"{log_prefix} Starting session: {self.session_name}")

        try:
            payload = {"name": self.session_name}
            if config:
                payload["config"] = config

            self._request("POST", "/api/sessions/start", payload)
            logger.info(f"{log_prefix} Session started: {self.session_name}")
            return True
        except WAHAError as e:
            logger.error(f"{log_prefix} Failed to start session: {e.message}")
            return False

    def stop_session(self) -> bool:
        """Stop WAHA session (keeps session data, can restart)."""
        log_prefix = self._get_log_prefix()
        logger.info(f"{log_prefix} Stopping session: {self.session_name}")

        try:
            self._request("POST", f"/api/sessions/{self.session_name}/stop")
            logger.info(f"{log_prefix} Session stopped: {self.session_name}")
            return True
        except WAHAError as e:
            logger.error(f"{log_prefix} Failed to stop session: {e.message}")
            return False

    def logout_session(self) -> bool:
        """Logout from WhatsApp (requires QR re-scan to reconnect)."""
        log_prefix = self._get_log_prefix()
        logger.info(f"{log_prefix} Logging out session: {self.session_name}")

        try:
            self._request("POST", "/api/sessions/logout", {"name": self.session_name})
            logger.info(f"{log_prefix} Session logged out: {self.session_name}")
            return True
        except WAHAError as e:
            logger.error(f"{log_prefix} Failed to logout session: {e.message}")
            return False

    def delete_session(self) -> bool:
        """Delete session completely (removes all session data)."""
        log_prefix = self._get_log_prefix()
        logger.info(f"{log_prefix} Deleting session: {self.session_name}")

        try:
            self._request("DELETE", f"/api/sessions/{self.session_name}")
            logger.info(f"{log_prefix} Session deleted: {self.session_name}")
            return True
        except WAHAError as e:
            logger.error(f"{log_prefix} Failed to delete session: {e.message}")
            return False

    def get_me(self) -> Optional[Dict]:
        """Get connected phone info."""
        try:
            return self._request("GET", f"/api/sessions/{self.session_name}/me")
        except WAHAError:
            return None

    @staticmethod
    def format_chat_id(phone: str) -> str:
        """Format phone number to WhatsApp chat ID.

        Args:
            phone: Phone number (e.g., 79001234567 or +79001234567)

        Returns:
            Chat ID with @c.us suffix (e.g., 79001234567@c.us)
        """
        clean = phone.replace("+", "").replace(" ", "").replace("-", "")
        return f"{clean}@c.us"

    @staticmethod
    def mask_phone(phone: str) -> str:
        """Mask phone number for logging.

        Args:
            phone: Phone number

        Returns:
            Masked phone (e.g., +7900123***)
        """
        clean = phone.lstrip("+")
        if len(clean) > 7:
            return f"+{clean[:7]}***"
        return f"+{clean}"
