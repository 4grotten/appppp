import asyncio
import logging
import os
import re
import tempfile
from datetime import date
from typing import Any, Dict, Optional, Tuple

import requests
from asgiref.sync import sync_to_async
from django.utils import timezone
from django.utils.text import slugify
from telethon import TelegramClient
from telethon.errors import (
    FloodWaitError,
    PasswordHashInvalidError,
    PhoneCodeExpiredError,
    PhoneCodeInvalidError,
    SessionPasswordNeededError,
)
from telethon.sessions import StringSession
from telethon.tl.types.auth import LoginTokenMigrateTo

# Telegram Datacenter IPs for reference
# DC1: 149.154.175.53 (Test)
# DC2: 149.154.167.51 (Europe - Netherlands)
# DC3: 149.154.175.100 (USA - Miami)
# DC4: 149.154.167.91 (Europe - Netherlands, files)
# DC5: 91.108.56.130 (Asia - Singapore)


def _run_async_unsafe(coro):
    old_value = os.environ.get("DJANGO_ALLOW_ASYNC_UNSAFE")
    os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

    try:
        # Create a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()
            asyncio.set_event_loop(None)
    finally:
        # Restore original value
        if old_value is None:
            os.environ.pop("DJANGO_ALLOW_ASYNC_UNSAFE", None)
        else:
            os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = old_value


async def _save_model(model, update_fields=None):
    """
    Save model - works in async context using sync_to_async.
    """
    if update_fields:
        await sync_to_async(model.save)(update_fields=update_fields)
    else:
        await sync_to_async(model.save)()


from messenger_bots.models import (
    BotCreationRequest,
    BotCreationStatus,
    TelegramUserbot,
    UserbotAuthState,
)

logger = logging.getLogger(__name__)

# BotFather's username
BOTFATHER_USERNAME = "BotFather"


class UserbotAuthService:
    """
    Service for managing Telegram userbot authentication.
    Handles the full auth flow: send code → verify code → 2FA (if needed).
    """

    def __init__(self, userbot: TelegramUserbot):
        self.userbot = userbot
        self.client: Optional[TelegramClient] = None

    def _create_client(self) -> TelegramClient:
        """Create a new Telethon client with connection timeout."""
        # Validate api_id and api_hash before creating client
        if not self.userbot.api_id or not self.userbot.api_hash:
            raise ValueError(
                "api_id and api_hash are required. Get them from https://my.telegram.org"
            )

        try:
            api_id = int(self.userbot.api_id)
        except (ValueError, TypeError):
            raise ValueError(
                f"Invalid api_id: '{self.userbot.api_id}'. Must be a number from https://my.telegram.org"
            )

        if api_id <= 0:
            raise ValueError(
                f"Invalid api_id: {api_id}. Get valid credentials from https://my.telegram.org"
            )

        session = StringSession(self.userbot.session_string or "")
        return TelegramClient(
            session,
            api_id,
            self.userbot.api_hash,
            timeout=30,  # Connection timeout in seconds
            connection_retries=2,
        )

    async def check_connection(self) -> Dict[str, Any]:
        """Check if userbot can connect and its current status."""
        try:
            self.client = self._create_client()
            await self.client.connect()

            is_authorized = await self.client.is_user_authorized()

            result = {
                "connected": True,
                "authorized": is_authorized,
                "user_info": None,
            }

            if is_authorized:
                me = await self.client.get_me()
                result["user_info"] = {
                    "id": me.id,
                    "first_name": me.first_name,
                    "last_name": me.last_name,
                    "username": me.username,
                    "phone": me.phone,
                }
                # Update session string if connected
                self.userbot.session_string = self.client.session.save()
                self.userbot.is_authenticated = True
                self.userbot.auth_state = UserbotAuthState.AUTHENTICATED
                await _save_model(
                    self.userbot,
                    update_fields=["session_string", "is_authenticated", "auth_state"],
                )

            return result

        except Exception as e:
            return {
                "connected": False,
                "authorized": False,
                "error": str(e),
            }
        finally:
            if self.client:
                await self.client.disconnect()

    async def send_code(self) -> Dict[str, Any]:
        """Step 1: Send verification code to the phone."""
        try:
            logger.info(
                f"[USERBOT_AUTH] Creating client for {self.userbot.phone_number}..."
            )
            self.client = self._create_client()

            logger.info("[USERBOT_AUTH] Connecting to Telegram (timeout=30s)...")
            await asyncio.wait_for(self.client.connect(), timeout=60)

            # Check if already authorized
            if await self.client.is_user_authorized():
                self.userbot.session_string = self.client.session.save()
                self.userbot.is_authenticated = True
                self.userbot.auth_state = UserbotAuthState.AUTHENTICATED
                self.userbot.auth_state_message = "Already authenticated!"
                await _save_model(
                    self.userbot,
                    update_fields=[
                        "session_string",
                        "is_authenticated",
                        "auth_state",
                        "auth_state_message",
                    ],
                )
                return {
                    "success": True,
                    "already_authenticated": True,
                    "message": "Already authenticated!",
                }

            # Send code request
            sent_code = await self.client.send_code_request(self.userbot.phone_number)

            # Extract delivery type info from Telegram response
            code_type = type(sent_code.type).__name__
            next_type = (
                type(sent_code.next_type).__name__ if sent_code.next_type else None
            )
            timeout = getattr(sent_code, "timeout", None)

            logger.info(
                f"[USERBOT_AUTH] Telegram response for {self.userbot.phone_number}: "
                f"type={code_type}, next_type={next_type}, timeout={timeout}, "
                f"hash_exists={bool(sent_code.phone_code_hash)}"
            )

            # Save phone_code_hash for later verification
            self.userbot.phone_code_hash = sent_code.phone_code_hash
            self.userbot.auth_state = UserbotAuthState.CODE_SENT
            self.userbot.auth_state_message = (
                f"Code sent to {self.userbot.phone_number}. Enter the code to continue."
            )
            self.userbot.last_error = None
            await _save_model(
                self.userbot,
                update_fields=[
                    "phone_code_hash",
                    "auth_state",
                    "auth_state_message",
                    "last_error",
                ],
            )

            return {
                "success": True,
                "message": f"Code sent to {self.userbot.phone_number}",
                "next_step": "verify_code",
                "telegram_response": {
                    "code_type": code_type,
                    "next_type": next_type,
                    "timeout": timeout,
                    "phone_code_hash_received": bool(sent_code.phone_code_hash),
                },
            }

        except asyncio.TimeoutError:
            error_msg = "Connection to Telegram timed out. Please check network connectivity to Telegram MTProto servers."
            logger.error(
                f"[USERBOT_AUTH] Timeout connecting for {self.userbot.phone_number}"
            )
            self.userbot.auth_state = UserbotAuthState.ERROR
            self.userbot.auth_state_message = error_msg
            self.userbot.last_error = error_msg
            await _save_model(
                self.userbot,
                update_fields=["auth_state", "auth_state_message", "last_error"],
            )
            return {"success": False, "error": error_msg}

        except ValueError as e:
            # Invalid api_id or api_hash
            error_msg = str(e)
            logger.error(
                f"[USERBOT_AUTH] Invalid credentials for {self.userbot.phone_number}: {error_msg}"
            )
            self.userbot.auth_state = UserbotAuthState.ERROR
            self.userbot.auth_state_message = error_msg
            self.userbot.last_error = error_msg
            await _save_model(
                self.userbot,
                update_fields=["auth_state", "auth_state_message", "last_error"],
            )
            return {"success": False, "error": error_msg}

        except FloodWaitError as e:
            error_msg = (
                f"Too many requests. Wait {e.seconds} seconds before trying again."
            )
            self.userbot.auth_state = UserbotAuthState.ERROR
            self.userbot.auth_state_message = error_msg
            self.userbot.last_error = error_msg
            await _save_model(
                self.userbot,
                update_fields=["auth_state", "auth_state_message", "last_error"],
            )
            return {"success": False, "error": error_msg}

        except Exception as e:
            error_msg = str(e)
            logger.error(
                f"[USERBOT_AUTH] Error for {self.userbot.phone_number}: {error_msg}"
            )
            self.userbot.auth_state = UserbotAuthState.ERROR
            self.userbot.auth_state_message = error_msg
            self.userbot.last_error = error_msg
            await _save_model(
                self.userbot,
                update_fields=["auth_state", "auth_state_message", "last_error"],
            )
            return {"success": False, "error": error_msg}

        finally:
            if self.client:
                await self.client.disconnect()

    async def qr_login_start(self, force_dc: int = None) -> Dict[str, Any]:
        """
        Start QR code login process.
        Returns a URL that should be encoded as QR code for user to scan.

        Args:
            force_dc: Force connection to specific datacenter (1-5).
                      DC2 = Europe (Netherlands), DC5 = Asia (Singapore)
                      Useful when user is in a region that requires specific DC.
        """
        try:
            logger.info("[QR_LOGIN] ====== QR LOGIN START ======")
            logger.info(
                f"[QR_LOGIN] Phone: {self.userbot.phone_number}, force_dc={force_dc}"
            )

            self.client = self._create_client()
            await self.client.connect()

            # Log initial session state
            initial_dc = getattr(self.client.session, "dc_id", "unknown")
            initial_server = getattr(self.client.session, "server_address", "unknown")
            logger.info(
                f"[QR_LOGIN] Connected. Initial session: DC{initial_dc}, server={initial_server}"
            )

            # Force specific datacenter if requested
            if force_dc and 1 <= force_dc <= 5:
                logger.info(
                    f"[QR_LOGIN] User requested force_dc={force_dc}, switching..."
                )
                try:
                    await self.client._switch_dc(force_dc)
                    new_dc = getattr(self.client.session, "dc_id", "unknown")
                    new_server = getattr(
                        self.client.session, "server_address", "unknown"
                    )
                    logger.info(
                        f"[QR_LOGIN] Force DC switch complete: DC{new_dc}, server={new_server}"
                    )
                except Exception as force_dc_err:
                    logger.error(
                        f"[QR_LOGIN] Force DC switch to DC{force_dc} FAILED: {force_dc_err}"
                    )
                    raise Exception(f"Failed to switch to DC{force_dc}: {force_dc_err}")

            # Check if already authorized
            if await self.client.is_user_authorized():
                logger.info("[QR_LOGIN] Already authorized, skipping QR generation")
                self.userbot.session_string = self.client.session.save()
                self.userbot.is_authenticated = True
                self.userbot.auth_state = UserbotAuthState.AUTHENTICATED
                self.userbot.auth_state_message = "Already authenticated!"
                await _save_model(
                    self.userbot,
                    update_fields=[
                        "session_string",
                        "is_authenticated",
                        "auth_state",
                        "auth_state_message",
                    ],
                )
                return {
                    "success": True,
                    "already_authenticated": True,
                    "message": "Already authenticated!",
                }

            # Start QR login with automatic datacenter migration handling
            logger.info("[QR_LOGIN] Calling client.qr_login()...")
            qr_login = await self.client.qr_login()
            current_dc = getattr(self.client.session, "dc_id", "unknown")

            # Detailed logging of Telegram response
            logger.info(f"[QR_LOGIN] Telegram response type: {type(qr_login).__name__}")
            logger.info(f"[QR_LOGIN] Telegram response object: {qr_login}")
            logger.info(f"[QR_LOGIN] Current session DC: {current_dc}")

            # Log all attributes of the response
            qr_attrs = {
                attr: getattr(qr_login, attr, "N/A")
                for attr in dir(qr_login)
                if not attr.startswith("_")
            }
            logger.info(f"[QR_LOGIN] Response attributes: {qr_attrs}")

            # Handle datacenter migration if Telegram requests it
            retry_count = 0
            while isinstance(qr_login, LoginTokenMigrateTo) and retry_count < 3:
                target_dc = qr_login.dc_id
                migrate_token = getattr(qr_login, "token", None)
                logger.info("[QR_LOGIN] *** MIGRATION REQUIRED ***")
                logger.info("[QR_LOGIN] LoginTokenMigrateTo received:")
                logger.info(f"[QR_LOGIN]   - target_dc: {target_dc}")
                logger.info(
                    f"[QR_LOGIN]   - token: {migrate_token[:20] if migrate_token else 'None'}..."
                )
                logger.info(f"[QR_LOGIN]   - attempt: {retry_count + 1}/3")

                # Switch to the requested datacenter
                try:
                    logger.info(f"[QR_LOGIN] Executing _switch_dc({target_dc})...")
                    await self.client._switch_dc(target_dc)

                    post_switch_dc = getattr(self.client.session, "dc_id", "unknown")
                    post_switch_server = getattr(
                        self.client.session, "server_address", "unknown"
                    )
                    logger.info(
                        f"[QR_LOGIN] DC switch SUCCESS: DC{post_switch_dc}, server={post_switch_server}"
                    )

                    # Retry QR login on new datacenter
                    logger.info(
                        f"[QR_LOGIN] Retrying qr_login() on DC{post_switch_dc}..."
                    )
                    qr_login = await self.client.qr_login()

                    logger.info(
                        f"[QR_LOGIN] Post-migration response type: {type(qr_login).__name__}"
                    )
                    logger.info(f"[QR_LOGIN] Post-migration response: {qr_login}")

                except Exception as switch_err:
                    logger.error(f"[QR_LOGIN] DC switch to DC{target_dc} FAILED!")
                    logger.error(f"[QR_LOGIN] Error type: {type(switch_err).__name__}")
                    logger.error(f"[QR_LOGIN] Error message: {switch_err}")
                    import traceback

                    logger.error(f"[QR_LOGIN] Traceback:\n{traceback.format_exc()}")
                    raise Exception(
                        f"Datacenter migration to DC{target_dc} failed: {switch_err}"
                    )

                retry_count += 1

            # Final check - do we have a valid QR login object?
            if isinstance(qr_login, LoginTokenMigrateTo):
                logger.error(
                    f"[QR_LOGIN] FAILED: Still getting LoginTokenMigrateTo after {retry_count} attempts"
                )
                logger.error(f"[QR_LOGIN] Final migration target: DC{qr_login.dc_id}")
                raise Exception(
                    f"Failed to complete datacenter migration after {retry_count} attempts. "
                    f"Try selecting a different region or contact support."
                )

            if not hasattr(qr_login, "url"):
                logger.error("[QR_LOGIN] FAILED: Response has no 'url' attribute")
                logger.error(f"[QR_LOGIN] Response type: {type(qr_login).__name__}")
                logger.error(f"[QR_LOGIN] Response: {qr_login}")
                raise Exception(
                    f"Unexpected response type: {type(qr_login).__name__}. "
                    "Please try again or use SMS authentication."
                )

            expires_str = None
            if hasattr(qr_login, "expires") and qr_login.expires:
                expires_str = qr_login.expires.isoformat()

            final_dc = getattr(self.client.session, "dc_id", "unknown")
            final_server = getattr(self.client.session, "server_address", "unknown")

            logger.info("[QR_LOGIN] ====== QR LOGIN SUCCESS ======")
            logger.info(f"[QR_LOGIN] Final DC: {final_dc}, server: {final_server}")
            logger.info(f"[QR_LOGIN] QR URL: {qr_login.url[:50]}...")
            logger.info(f"[QR_LOGIN] Expires: {expires_str}")

            # CRITICAL: Save session_string so qr_login_check() can reconnect
            # with the same session that generated the QR code
            self.userbot.session_string = self.client.session.save()
            self.userbot.auth_state = UserbotAuthState.CODE_SENT
            self.userbot.auth_state_message = (
                f"Scan QR code with Telegram app (DC{final_dc})."
            )
            self.userbot.last_error = None
            await _save_model(
                self.userbot,
                update_fields=[
                    "session_string",
                    "auth_state",
                    "auth_state_message",
                    "last_error",
                ],
            )

            return {
                "success": True,
                "qr_url": qr_login.url,
                "expires": expires_str,
                "datacenter": final_dc,
                "message": f"QR code generated on DC{final_dc}. Scan with Telegram app.",
                "next_step": "qr_wait",
            }

        except FloodWaitError as e:
            error_msg = (
                f"Too many requests. Wait {e.seconds} seconds before trying again."
            )
            self.userbot.auth_state = UserbotAuthState.ERROR
            self.userbot.auth_state_message = error_msg
            self.userbot.last_error = error_msg
            await _save_model(
                self.userbot,
                update_fields=["auth_state", "auth_state_message", "last_error"],
            )
            return {"success": False, "error": error_msg}

        except Exception as e:
            error_msg = str(e)
            self.userbot.auth_state = UserbotAuthState.ERROR
            self.userbot.auth_state_message = error_msg
            self.userbot.last_error = error_msg
            await _save_model(
                self.userbot,
                update_fields=["auth_state", "auth_state_message", "last_error"],
            )
            return {"success": False, "error": error_msg}

        finally:
            if self.client:
                await self.client.disconnect()

    async def qr_login_check(self) -> Dict[str, Any]:
        """
        Check if user has scanned QR code and is now authorized.
        This only checks authorization status, doesn't generate new QR.
        """
        try:
            logger.info("[QR_CHECK] ====== QR CHECK START ======")
            logger.info(f"[QR_CHECK] Phone: {self.userbot.phone_number}")

            self.client = self._create_client()
            await self.client.connect()

            session_dc = getattr(self.client.session, "dc_id", "unknown")
            session_server = getattr(self.client.session, "server_address", "unknown")
            logger.info(
                f"[QR_CHECK] Connected to DC{session_dc}, server={session_server}"
            )

            # Check if authorized (user scanned QR)
            logger.info("[QR_CHECK] Checking is_user_authorized()...")
            is_authorized = await self.client.is_user_authorized()
            logger.info(f"[QR_CHECK] is_user_authorized() = {is_authorized}")

            if is_authorized:
                self.userbot.session_string = self.client.session.save()
                self.userbot.is_authenticated = True
                self.userbot.auth_state = UserbotAuthState.AUTHENTICATED
                self.userbot.auth_state_message = "Successfully authenticated via QR!"
                self.userbot.last_error = None
                await _save_model(
                    self.userbot,
                    update_fields=[
                        "session_string",
                        "is_authenticated",
                        "auth_state",
                        "auth_state_message",
                        "last_error",
                    ],
                )

                me = await self.client.get_me()
                logger.info("[QR_CHECK] ====== QR CHECK SUCCESS ======")
                logger.info(
                    f"[QR_CHECK] Authenticated as: {me.first_name} (@{me.username}), id={me.id}"
                )
                return {
                    "success": True,
                    "message": f"Successfully authenticated as {me.first_name}!",
                    "user_info": {
                        "id": me.id,
                        "first_name": me.first_name,
                        "username": me.username,
                    },
                }

            # Not yet authorized - user hasn't scanned
            logger.info("[QR_CHECK] Not yet authorized - QR not scanned")
            return {
                "success": False,
                "not_scanned": True,
                "error": "QR code not scanned yet. Please scan and try again.",
            }

        except SessionPasswordNeededError:
            # 2FA is enabled - need password
            logger.info("[QR_CHECK] 2FA required - SessionPasswordNeededError")
            self.userbot.auth_state = UserbotAuthState.AWAITING_2FA
            self.userbot.auth_state_message = (
                "2FA is enabled. Enter your password to continue."
            )
            await _save_model(
                self.userbot, update_fields=["auth_state", "auth_state_message"]
            )
            return {
                "success": False,
                "needs_2fa": True,
                "message": "2FA is enabled. Please enter your password.",
                "next_step": "verify_2fa",
            }

        except Exception as e:
            error_msg = str(e)
            logger.error("[QR_CHECK] ====== QR CHECK FAILED ======")
            logger.error(f"[QR_CHECK] Error type: {type(e).__name__}")
            logger.error(f"[QR_CHECK] Error message: {error_msg}")
            import traceback

            logger.error(f"[QR_CHECK] Traceback:\n{traceback.format_exc()}")
            self.userbot.last_error = error_msg
            await _save_model(self.userbot, update_fields=["last_error"])
            return {"success": False, "error": error_msg}

        finally:
            if self.client:
                await self.client.disconnect()

    async def verify_code(self, code: str) -> Dict[str, Any]:
        """Step 2: Verify the code sent to phone."""
        if not self.userbot.phone_code_hash:
            return {
                "success": False,
                "error": "No code was sent. Please send code first.",
            }

        try:
            self.client = self._create_client()
            await self.client.connect()

            # Try to sign in with code
            try:
                await self.client.sign_in(
                    phone=self.userbot.phone_number,
                    code=code,
                    phone_code_hash=self.userbot.phone_code_hash,
                )

                # Success - save session
                self.userbot.session_string = self.client.session.save()
                self.userbot.is_authenticated = True
                self.userbot.auth_state = UserbotAuthState.AUTHENTICATED
                self.userbot.auth_state_message = "Successfully authenticated!"
                self.userbot.phone_code_hash = None
                self.userbot.last_error = None
                await _save_model(
                    self.userbot,
                    update_fields=[
                        "session_string",
                        "is_authenticated",
                        "auth_state",
                        "auth_state_message",
                        "phone_code_hash",
                        "last_error",
                    ],
                )

                me = await self.client.get_me()
                return {
                    "success": True,
                    "message": "Successfully authenticated!",
                    "user_info": {
                        "id": me.id,
                        "first_name": me.first_name,
                        "username": me.username,
                    },
                }

            except SessionPasswordNeededError:
                # 2FA is enabled
                self.userbot.auth_state = UserbotAuthState.AWAITING_2FA
                self.userbot.auth_state_message = (
                    "2FA is enabled. Enter your password to continue."
                )
                await _save_model(
                    self.userbot, update_fields=["auth_state", "auth_state_message"]
                )
                return {
                    "success": False,
                    "needs_2fa": True,
                    "message": "2FA is enabled. Please enter your password.",
                    "next_step": "verify_2fa",
                }

        except PhoneCodeInvalidError:
            return {"success": False, "error": "Invalid code. Please try again."}

        except PhoneCodeExpiredError:
            self.userbot.auth_state = UserbotAuthState.NOT_STARTED
            self.userbot.phone_code_hash = None
            self.userbot.auth_state_message = "Code expired. Please request a new one."
            await _save_model(
                self.userbot,
                update_fields=["auth_state", "phone_code_hash", "auth_state_message"],
            )
            return {
                "success": False,
                "error": "Code expired. Please request a new one.",
            }

        except Exception as e:
            error_msg = str(e)
            self.userbot.last_error = error_msg
            await _save_model(self.userbot, update_fields=["last_error"])
            return {"success": False, "error": error_msg}

        finally:
            if self.client:
                await self.client.disconnect()

    async def verify_2fa(self, password: str) -> Dict[str, Any]:
        """Step 3: Verify 2FA password (if enabled)."""
        if self.userbot.auth_state != UserbotAuthState.AWAITING_2FA:
            return {
                "success": False,
                "error": "Not awaiting 2FA. Please start from the beginning.",
            }

        try:
            self.client = self._create_client()
            await self.client.connect()

            # Sign in with password
            await self.client.sign_in(password=password)

            # Success - save session
            self.userbot.session_string = self.client.session.save()
            self.userbot.is_authenticated = True
            self.userbot.auth_state = UserbotAuthState.AUTHENTICATED
            self.userbot.auth_state_message = "Successfully authenticated with 2FA!"
            self.userbot.phone_code_hash = None
            self.userbot.last_error = None
            await _save_model(
                self.userbot,
                update_fields=[
                    "session_string",
                    "is_authenticated",
                    "auth_state",
                    "auth_state_message",
                    "phone_code_hash",
                    "last_error",
                ],
            )

            me = await self.client.get_me()
            return {
                "success": True,
                "message": "Successfully authenticated with 2FA!",
                "user_info": {
                    "id": me.id,
                    "first_name": me.first_name,
                    "username": me.username,
                },
            }

        except PasswordHashInvalidError:
            return {"success": False, "error": "Invalid password. Please try again."}

        except Exception as e:
            error_msg = str(e)
            self.userbot.last_error = error_msg
            await _save_model(self.userbot, update_fields=["last_error"])
            return {"success": False, "error": error_msg}

        finally:
            if self.client:
                await self.client.disconnect()

    async def logout(self) -> Dict[str, Any]:
        """Logout and clear session."""
        try:
            if self.userbot.session_string:
                self.client = self._create_client()
                await self.client.connect()
                await self.client.log_out()

            self.userbot.reset_auth_state()
            await _save_model(self.userbot)

            return {"success": True, "message": "Successfully logged out."}

        except Exception as e:
            # Even if logout fails, clear local session
            self.userbot.reset_auth_state()
            await _save_model(self.userbot)
            return {
                "success": True,
                "message": f"Session cleared. Telegram logout: {e}",
            }

        finally:
            if self.client:
                await self.client.disconnect()

    async def get_dialogs(self, limit: int = 20) -> Dict[str, Any]:
        """Get recent dialogs/chats for debugging."""
        if not self.userbot.is_authenticated:
            return {"success": False, "error": "Not authenticated."}

        try:
            self.client = self._create_client()
            await self.client.connect()

            if not await self.client.is_user_authorized():
                return {"success": False, "error": "Session invalid. Re-authenticate."}

            dialogs = await self.client.get_dialogs(limit=limit)
            dialog_list = []
            for dialog in dialogs:
                dialog_list.append(
                    {
                        "name": dialog.name,
                        "id": dialog.id,
                        "is_user": dialog.is_user,
                        "is_group": dialog.is_group,
                        "is_channel": dialog.is_channel,
                        "unread_count": dialog.unread_count,
                    }
                )

            return {"success": True, "dialogs": dialog_list}

        except Exception as e:
            return {"success": False, "error": str(e)}

        finally:
            if self.client:
                await self.client.disconnect()

    async def send_test_message(self, chat: str, message: str) -> Dict[str, Any]:
        """Send a test message (for debugging)."""
        if not self.userbot.is_authenticated:
            return {"success": False, "error": "Not authenticated."}

        try:
            self.client = self._create_client()
            await self.client.connect()

            if not await self.client.is_user_authorized():
                return {"success": False, "error": "Session invalid. Re-authenticate."}

            await self.client.send_message(chat, message)
            return {"success": True, "message": f"Message sent to {chat}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

        finally:
            if self.client:
                await self.client.disconnect()


class BotFactoryService:
    """
    Service for automated bot creation via Telegram userbot + BotFather.
    Uses Telethon to communicate with @BotFather.
    """

    def __init__(self, userbot: TelegramUserbot):
        self.userbot = userbot
        self.client: Optional[TelegramClient] = None

    async def _get_client(self) -> TelegramClient:
        """Get or create Telethon client."""
        if self.client and self.client.is_connected():
            return self.client

        session = StringSession(self.userbot.session_string or "")
        self.client = TelegramClient(
            session,
            int(self.userbot.api_id),
            self.userbot.api_hash,
        )
        await self.client.connect()

        if not await self.client.is_user_authorized():
            raise Exception("Userbot is not authenticated. Please authenticate first.")

        return self.client

    async def disconnect(self):
        """Disconnect the client."""
        if self.client and self.client.is_connected():
            await self.client.disconnect()

    async def authenticate(
        self, phone_code: str = None, password: str = None
    ) -> Tuple[bool, str]:
        """
        Authenticate the userbot.
        Call first without code to send SMS, then with code to complete auth.
        """
        try:
            session = StringSession(self.userbot.session_string or "")
            self.client = TelegramClient(
                session,
                int(self.userbot.api_id),
                self.userbot.api_hash,
            )
            await self.client.connect()

            if await self.client.is_user_authorized():
                # Already authenticated, save session
                self.userbot.session_string = self.client.session.save()
                self.userbot.is_authenticated = True
                await _save_model(
                    self.userbot, update_fields=["session_string", "is_authenticated"]
                )
                return True, "Already authenticated"

            if phone_code is None:
                # Send code request
                await self.client.send_code_request(self.userbot.phone_number)
                return (
                    False,
                    "Code sent to phone. Call again with phone_code parameter.",
                )

            # Sign in with code
            try:
                await self.client.sign_in(self.userbot.phone_number, phone_code)
            except Exception as e:
                if "password" in str(e).lower() or "2fa" in str(e).lower():
                    if password:
                        await self.client.sign_in(password=password)
                    else:
                        return False, "2FA enabled. Call again with password parameter."
                else:
                    raise

            # Save session string
            self.userbot.session_string = self.client.session.save()
            self.userbot.is_authenticated = True
            await _save_model(
                self.userbot, update_fields=["session_string", "is_authenticated"]
            )

            return True, "Successfully authenticated"

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            self.userbot.last_error = str(e)
            await _save_model(self.userbot, update_fields=["last_error"])
            return False, str(e)

    async def create_bot(self, request: BotCreationRequest) -> Tuple[bool, str]:
        """
        Create a new bot via BotFather.

        Flow:
        1. Send /newbot to @BotFather
        2. Send bot name (org title + APZ)
        3. Send bot username
        4. Parse token from response
        """
        logger.info("[BOT_FACTORY] ====== CREATE BOT START ======")
        logger.info(
            f"[BOT_FACTORY] Request id={request.id}, org_id={request.organization_id}"
        )
        logger.info(f"[BOT_FACTORY] Bot name: '{request.bot_name}'")
        logger.info(f"[BOT_FACTORY] Using userbot: {self.userbot.phone_number}")

        try:
            logger.info("[BOT_FACTORY] Step 0: Getting Telethon client...")
            client = await self._get_client()
            logger.info("[BOT_FACTORY] Client connected successfully")

            # Update request status
            request.status = BotCreationStatus.IN_PROGRESS
            request.userbot_used = self.userbot
            await _save_model(request, update_fields=["status", "userbot_used"])
            logger.info("[BOT_FACTORY] Request status updated to IN_PROGRESS")

            # Generate bot username
            org_slug = slugify(request.organization.title).replace("-", "_")
            if len(org_slug) > 20:
                org_slug = org_slug[:20]
            logger.debug(f"[BOT_FACTORY] Org slug: '{org_slug}'")

            # Try different username variations
            base_username = f"{org_slug}_apz_bot"
            username_attempts = [
                base_username,
                f"{org_slug}_apofiz_bot",
                f"apz_{org_slug}_bot",
                f"{org_slug}{request.organization.id}_apz_bot",
            ]
            logger.info(f"[BOT_FACTORY] Username attempts: {username_attempts}")

            # Get BotFather entity
            logger.info("[BOT_FACTORY] Getting BotFather entity...")
            botfather = await client.get_entity(BOTFATHER_USERNAME)
            logger.info(f"[BOT_FACTORY] BotFather entity obtained: id={botfather.id}")

            # Step 1: Send /newbot
            logger.info("[BOT_FACTORY] Step 1: Sending /newbot to BotFather...")
            await client.send_message(botfather, "/newbot")
            await asyncio.sleep(2)

            # Get response
            messages = await client.get_messages(botfather, limit=1)
            if not messages:
                raise Exception("No response from BotFather")
            logger.debug(
                f"[BOT_FACTORY] BotFather response: {messages[0].text[:100] if messages[0].text else 'None'}..."
            )

            # Step 2: Send bot name
            logger.info(
                f"[BOT_FACTORY] Step 2: Sending bot name '{request.bot_name}'..."
            )
            await client.send_message(botfather, request.bot_name)
            await asyncio.sleep(2)

            # Step 3: Try usernames until one works
            bot_token = None
            final_username = None

            for i, username in enumerate(username_attempts):
                logger.info(
                    f"[BOT_FACTORY] Step 3.{i+1}: Trying username '{username}'..."
                )
                await client.send_message(botfather, username)
                await asyncio.sleep(3)

                # Check response
                messages = await client.get_messages(botfather, limit=1)
                if not messages:
                    logger.warning(
                        f"[BOT_FACTORY] No response from BotFather for username '{username}'"
                    )
                    continue

                response_text = messages[0].text or ""
                logger.debug(
                    f"[BOT_FACTORY] BotFather response: {response_text[:200]}..."
                )

                # Check if username was taken
                if (
                    "sorry" in response_text.lower()
                    and "taken" in response_text.lower()
                ):
                    logger.info(
                        f"[BOT_FACTORY] Username '{username}' is TAKEN, trying next..."
                    )
                    continue

                # Check if we got a token
                token_match = re.search(r"(\d+:[A-Za-z0-9_-]+)", response_text)
                if token_match:
                    bot_token = token_match.group(1)
                    final_username = username
                    logger.info(
                        f"[BOT_FACTORY] SUCCESS! Token obtained: {bot_token[:20]}..."
                    )
                    break

                # If error but not "taken", might be rate limit or other issue
                if "error" in response_text.lower():
                    logger.error(f"[BOT_FACTORY] BotFather error: {response_text}")
                    raise Exception(f"BotFather error: {response_text}")

            if not bot_token:
                logger.error(
                    "[BOT_FACTORY] ERROR: All usernames taken or error occurred"
                )
                raise Exception(
                    "Failed to create bot - all usernames taken or error occurred"
                )

            # Update request with success
            request.status = BotCreationStatus.COMPLETED
            request.bot_username = final_username
            request.bot_token = bot_token
            request.completed_at = timezone.now()
            await _save_model(
                request,
                update_fields=["status", "bot_username", "bot_token", "completed_at"],
            )
            logger.info(
                f"[BOT_FACTORY] Request updated: status=COMPLETED, username=@{final_username}"
            )

            # Update userbot stats
            self.userbot.bots_created_today += 1
            self.userbot.total_bots_created += 1
            self.userbot.last_used_at = timezone.now()
            await _save_model(
                self.userbot,
                update_fields=[
                    "bots_created_today",
                    "total_bots_created",
                    "last_used_at",
                ],
            )
            logger.info(
                f"[BOT_FACTORY] Userbot stats updated: today={self.userbot.bots_created_today}/20, total={self.userbot.total_bots_created}"
            )

            # Try to set bot avatar from organization image
            await self._set_bot_avatar(
                client, botfather, final_username, request.organization
            )

            logger.info("[BOT_FACTORY] ====== CREATE BOT SUCCESS ======")
            logger.info(
                f"[BOT_FACTORY] Created bot @{final_username} for org {request.organization.id}"
            )
            return True, bot_token

        except Exception as e:
            logger.error("[BOT_FACTORY] ====== CREATE BOT FAILED ======")
            logger.error(f"[BOT_FACTORY] ERROR: {e}", exc_info=True)
            request.status = BotCreationStatus.FAILED
            request.error_message = str(e)
            await _save_model(request, update_fields=["status", "error_message"])

            self.userbot.last_error = str(e)
            await _save_model(self.userbot, update_fields=["last_error"])

            return False, str(e)

        finally:
            await self.disconnect()

    async def _set_bot_avatar(
        self, client: TelegramClient, botfather, bot_username: str, organization
    ) -> bool:
        """
        Set bot avatar using organization image via BotFather.

        Flow:
        1. Download organization image
        2. Send /setuserpic to BotFather
        3. Send bot username
        4. Send the image file
        """
        try:
            # Get organization image URL
            @sync_to_async
            def get_org_image_url():
                if organization.image and organization.image.file:
                    return organization.image.file.url
                return None

            image_url = await get_org_image_url()

            if not image_url:
                logger.info(
                    "[BOT_FACTORY] No organization image, skipping avatar setup"
                )
                return False

            logger.info(f"[BOT_FACTORY] Setting bot avatar from: {image_url[:50]}...")

            # Download image to temp file
            response = requests.get(image_url, timeout=30)
            if response.status_code != 200:
                logger.warning(
                    f"[BOT_FACTORY] Failed to download image: {response.status_code}"
                )
                return False

            # Save to temp file
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_file:
                tmp_file.write(response.content)
                tmp_path = tmp_file.name

            try:
                # Step 1: Send /setuserpic
                logger.info("[BOT_FACTORY] Sending /setuserpic to BotFather...")
                await client.send_message(botfather, "/setuserpic")
                await asyncio.sleep(2)

                # Step 2: Send bot username
                logger.info(f"[BOT_FACTORY] Sending bot username @{bot_username}...")
                await client.send_message(botfather, f"@{bot_username}")
                await asyncio.sleep(2)

                # Step 3: Send the image
                logger.info("[BOT_FACTORY] Sending avatar image...")
                await client.send_file(botfather, tmp_path)
                await asyncio.sleep(2)

                # Check response
                messages = await client.get_messages(botfather, limit=1)
                response_text = (
                    messages[0].text if messages and messages[0].text else ""
                )

                if (
                    "success" in response_text.lower()
                    or "done" in response_text.lower()
                ):
                    logger.info("[BOT_FACTORY] Bot avatar set successfully!")
                    return True
                else:
                    logger.info(f"[BOT_FACTORY] Avatar response: {response_text[:100]}")
                    return True  # Assume success if no error

            finally:
                # Clean up temp file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        except Exception as e:
            logger.warning(f"[BOT_FACTORY] Failed to set bot avatar: {e}")
            return False

    @classmethod
    async def get_available_userbot(cls) -> Optional[TelegramUserbot]:
        """Get an available userbot for bot creation."""
        logger.info("[BOT_FACTORY] Looking for available userbot...")
        # Reset daily counter if new day
        today = date.today()

        @sync_to_async
        def get_userbots():
            return list(
                TelegramUserbot.objects.filter(
                    is_active=True,
                    is_authenticated=True,
                    bots_created_today__lt=20,  # BotFather daily limit
                ).order_by("bots_created_today", "last_used_at")
            )

        userbots = await get_userbots()

        logger.info(f"[BOT_FACTORY] Found {len(userbots)} candidate userbots")

        for userbot in userbots:
            logger.debug(
                f"[BOT_FACTORY] Checking userbot: {userbot.phone_number}, today={userbot.bots_created_today}/20"
            )
            # Check if counter needs reset (new day)
            if userbot.last_used_at and userbot.last_used_at.date() < today:
                logger.info(
                    f"[BOT_FACTORY] Resetting daily counter for {userbot.phone_number} (last used: {userbot.last_used_at.date()})"
                )
                userbot.bots_created_today = 0
                await _save_model(userbot, update_fields=["bots_created_today"])

            if userbot.bots_created_today < 20:
                logger.info(
                    f"[BOT_FACTORY] Selected userbot: {userbot.phone_number} ({userbot.bots_created_today}/20 today)"
                )
                return userbot

        logger.warning("[BOT_FACTORY] No available userbots found!")
        return None

    @classmethod
    def create_bot_sync(cls, request: BotCreationRequest) -> Tuple[bool, str]:
        """Synchronous wrapper for create_bot."""
        logger.info(f"[BOT_FACTORY] create_bot_sync called for request id={request.id}")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(cls._create_bot_async(request))
        finally:
            loop.close()

    @classmethod
    async def _create_bot_async(cls, request: BotCreationRequest) -> Tuple[bool, str]:
        """Async bot creation with userbot selection."""
        logger.info(
            f"[BOT_FACTORY] _create_bot_async called for request id={request.id}"
        )
        userbot = await cls.get_available_userbot()
        if not userbot:
            logger.error(
                f"[BOT_FACTORY] ERROR: No available userbots for request {request.id}"
            )
            request.status = BotCreationStatus.FAILED
            request.error_message = "No available userbots. Please try again later."
            await _save_model(request, update_fields=["status", "error_message"])
            return False, "No available userbots"

        logger.info(
            f"[BOT_FACTORY] Starting bot creation with userbot {userbot.phone_number}"
        )
        service = cls(userbot)
        return await service.create_bot(request)
