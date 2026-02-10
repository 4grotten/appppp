"""Celery tasks for OTP Bot service."""

import base64
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

from celery import shared_task
from django.utils import timezone

from .models import OTPCode, ChatSession
from .webhook_handler import get_waha_client, get_ai_service, get_elevenlabs_service

logger = logging.getLogger(__name__)


@shared_task(time_limit=60, soft_time_limit=50)
def cleanup_expired_otp_codes():
    """Delete expired OTP codes from database.

    Run periodically via Celery Beat (e.g., every hour).
    """
    count, _ = OTPCode.objects.filter(
        expires_at__lt=timezone.now()
    ).delete()
    if count:
        logger.info(f"[OTP_CLEANUP] Deleted {count} expired OTP codes")
    return {"deleted": count}


@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=5,
    time_limit=150,
    soft_time_limit=120,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=30,
    retry_jitter=True,
)
def process_otp_voice_message_task(
    self,
    phone: str,
    message_id: str,
    payload: dict,
):
    """Process voice message asynchronously (STT -> AI -> TTS -> Send).

    Offloaded from webhook handler to avoid blocking.
    Downloads audio via multiple fallback methods, then processes.

    Features:
    - Automatic retry with exponential backoff on failures
    - Time limits to prevent worker blocking
    - Multiple audio download fallback methods

    Args:
        phone: User's phone number (without + prefix)
        message_id: WhatsApp message ID
        payload: Full message payload from webhook
    """
    masked_phone = f"+{phone[:7]}***" if len(phone) > 7 else f"+{phone}"
    logger.info(f"[OTP_VOICE_TASK] Processing voice from {masked_phone}")

    # Use singleton services (optimization #1)
    waha = get_waha_client()
    ai = get_ai_service()
    elevenlabs = get_elevenlabs_service()

    # Check if ElevenLabs is configured
    if not elevenlabs.is_configured():
        logger.warning("[OTP_VOICE_TASK] ElevenLabs not configured")
        waha.send_text(
            f"+{phone}",
            "Голосовые сообщения временно недоступны. Пожалуйста, напишите текстом."
        )
        return {"success": False, "error": "ElevenLabs not configured"}

    # Download audio using multiple fallback methods
    audio_bytes = _download_voice_audio(phone, message_id, payload, waha)

    if not audio_bytes:
        logger.error(f"[OTP_VOICE_TASK] Failed to download audio for {masked_phone}")
        waha.send_text(
            f"+{phone}",
            "Не удалось загрузить голосовое сообщение. Попробуйте ещё раз или напишите текстом."
        )
        return {"success": False, "error": "Failed to download audio"}

    # Speech-to-Text
    logger.info(f"[OTP_VOICE_TASK] Transcribing {len(audio_bytes)} bytes")
    transcribed_text = elevenlabs.speech_to_text(audio_bytes)

    if not transcribed_text:
        logger.warning(f"[OTP_VOICE_TASK] STT failed for {masked_phone}")
        waha.send_text(
            f"+{phone}",
            "Не удалось распознать речь. Попробуйте говорить чётче или напишите текстом."
        )
        return {"success": False, "error": "STT failed"}

    logger.info(f"[OTP_VOICE_TASK] Transcribed: {transcribed_text[:50]}...")

    # Get chat session and add message
    session = ChatSession.get_or_create_session(phone)
    session.add_message("user", transcribed_text)

    # Get AI response
    response = ai.get_response(
        phone_number=phone,
        question=transcribed_text,
        chat_history=session.get_history()[:-1],
        voice_mode=True,
    )
    session.add_message("assistant", response)

    # Text-to-Speech
    logger.info(f"[OTP_VOICE_TASK] TTS for response: {len(response)} chars")
    audio_response = elevenlabs.text_to_speech(response)

    if audio_response:
        success = waha.send_voice_base64(f"+{phone}", audio_response)
        if success:
            logger.info(f"[OTP_VOICE_TASK] Voice response sent to {masked_phone}")
            return {"success": True, "transcribed": transcribed_text[:50]}
        else:
            logger.warning(f"[OTP_VOICE_TASK] Voice send failed, falling back to text")

    # Fallback to text
    waha.send_text(f"+{phone}", response)
    logger.info(f"[OTP_VOICE_TASK] Text response sent to {masked_phone}")
    return {"success": True, "fallback_to_text": True}


@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=3,
    time_limit=90,
    soft_time_limit=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=15,
)
def process_otp_text_message_task(
    self,
    phone: str,
    text: str,
):
    """Process text message asynchronously (AI response + optional TTS).

    Offloaded from webhook handler for fast webhook response time.
    AI calls can take 1-5 seconds, which would block the webhook.

    Args:
        phone: User's phone number (without + prefix)
        text: User's message text
    """
    from .models import UserVoicePreference

    masked_phone = f"+{phone[:7]}***" if len(phone) > 7 else f"+{phone}"
    logger.info(f"[OTP_TEXT_TASK] Processing text from {masked_phone}: {text[:30]}...")

    # Use singleton services (optimization #1)
    waha = get_waha_client()
    ai = get_ai_service()
    elevenlabs = get_elevenlabs_service()

    # Get voice preference inside task (optimization #6)
    pref = UserVoicePreference.get_preference(phone)
    voice_mode = pref.voice_enabled

    # Get or create chat session
    session = ChatSession.get_or_create_session(phone)
    session.add_message("user", text)

    # Get AI response
    response = ai.get_response(
        phone_number=phone,
        question=text,
        chat_history=session.get_history()[:-1],
        voice_mode=voice_mode,
    )
    session.add_message("assistant", response)

    # Send response based on voice mode
    if voice_mode and elevenlabs.is_configured():
        logger.info(f"[OTP_TEXT_TASK] TTS for {masked_phone}: {len(response)} chars")
        audio_bytes = elevenlabs.text_to_speech(response)

        if audio_bytes:
            success = waha.send_voice_base64(f"+{phone}", audio_bytes)
            if success:
                logger.info(f"[OTP_TEXT_TASK] Voice response sent to {masked_phone}")
                return {"success": True, "voice": True}
            else:
                logger.warning(f"[OTP_TEXT_TASK] Voice send failed, falling back to text")

    # Send text response
    waha.send_text(f"+{phone}", response)
    logger.info(f"[OTP_TEXT_TASK] Text response sent to {masked_phone}")
    return {"success": True, "voice": False}


def _download_voice_audio(
    phone: str,
    message_id: str,
    payload: dict,
    waha,
) -> Optional[bytes]:
    """Download voice audio using parallel fallback methods (optimization #4).

    Uses ThreadPoolExecutor for parallel attempts:
    - First successful method wins
    - Fallback sequential methods for edge cases

    Args:
        phone: User's phone number
        message_id: WhatsApp message ID
        payload: Full webhook payload
        waha: WAHAOTPClient instance

    Returns:
        Audio bytes or None
    """
    from messenger_bots.services.whatsapp.http_client import waha_request

    masked_phone = f"+{phone[:7]}***" if len(phone) > 7 else f"+{phone}"

    def try_base64():
        media_data = payload.get("media", {}).get("data")
        if media_data:
            try:
                return base64.b64decode(media_data)
            except Exception:
                return None
        return None

    def try_media_url():
        url = payload.get("media", {}).get("url")
        if url:
            try:
                resp = waha_request("GET", url, timeout=(3, 15))
                return resp.content if resp.ok else None
            except Exception:
                return None
        return None

    def try_media_url_root():
        url = payload.get("mediaUrl")
        if url:
            try:
                resp = waha_request("GET", url, timeout=(3, 15))
                return resp.content if resp.ok else None
            except Exception:
                return None
        return None

    def try_waha_api():
        return waha.download_media(message_id)

    def try_waha_cus():
        msg_id_cus = message_id.replace("@s.whatsapp.net", "@c.us")
        if msg_id_cus != message_id:
            return waha.download_media(msg_id_cus)
        return None

    def try_raw_id():
        parts = message_id.split("_")
        if len(parts) >= 3:
            return waha.download_media(parts[-1])
        return None

    # Parallel execution - first success wins
    methods = [try_base64, try_media_url, try_media_url_root, try_waha_api]

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(m): m.__name__ for m in methods}

        for future in as_completed(futures, timeout=20):
            try:
                result = future.result()
                if result:
                    logger.info(f"[VOICE_DL] Success via {futures[future]}: {len(result)} bytes")
                    return result
            except Exception:
                pass

    # Fallback sequential methods
    for method in [try_waha_cus, try_raw_id]:
        try:
            result = method()
            if result:
                logger.info(f"[VOICE_DL] Fallback success via {method.__name__}: {len(result)} bytes")
                return result
        except Exception:
            pass

    logger.error(f"[VOICE_DL] All download methods failed for {masked_phone}")
    return None


@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=3,
    time_limit=30,
    soft_time_limit=25,
)
def send_welcome_message_task(self, phone_number: str):
    """Send welcome message with buttons to new user after OTP verification.

    Called asynchronously after OTP code is verified for a new user.
    Tries to send interactive message with "Get Card" button first,
    falls back to plain text if buttons are not supported.

    Args:
        phone_number: User's phone number in E.164 format (e.g., +79991234567)
    """
    from .services.otp_service import OTPService

    masked_phone = f"{phone_number[:7]}***" if len(phone_number) > 7 else phone_number
    logger.info(f"[OTP_WELCOME] Sending welcome message to {masked_phone}")

    try:
        service = OTPService()

        # Try sending with interactive buttons first
        sent = service.send_welcome_with_card_button(phone_number)

        if not sent:
            # Fallback to plain text welcome
            logger.info(f"[OTP_WELCOME] Buttons failed, trying plain text for {masked_phone}")
            sent = service.send_welcome_message(phone_number)

        if sent:
            logger.info(f"[OTP_WELCOME] Welcome message sent successfully to {masked_phone}")
            return {"status": "sent", "phone": masked_phone}
        else:
            logger.warning(f"[OTP_WELCOME] Failed to send welcome message to {masked_phone}")
            return {"status": "failed", "phone": masked_phone}

    except Exception as e:
        logger.error(f"[OTP_WELCOME] Error sending welcome message to {masked_phone}: {e}")
        raise self.retry(exc=e)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=5,
    time_limit=30,
    soft_time_limit=25,
)
def send_transaction_notification_task(
    self,
    phone_number: str,
    tx_type: str,
    amount: float,
    currency: str = "AED",
    merchant: str = None,
    balance_after: float = None,
):
    """Send transaction notification via WhatsApp.

    Called by EasyCard webhook handler to notify user about transactions.
    Uses interactive buttons with fallback to plain text.

    Args:
        phone_number: User's phone number in E.164 format
        tx_type: Transaction type (top_up, card_payment, etc.)
        amount: Transaction amount
        currency: Currency code
        merchant: Optional merchant name
        balance_after: Optional balance after transaction
    """
    from .services.otp_service import OTPService

    masked_phone = f"{phone_number[:7]}***" if len(phone_number) > 7 else phone_number
    logger.info(
        f"[OTP_TX_NOTIFY] Sending notification to {masked_phone}: "
        f"{tx_type} {amount} {currency}"
    )

    try:
        service = OTPService()
        sent = service.send_transaction_notification(
            phone_number=phone_number,
            tx_type=tx_type,
            amount=amount,
            currency=currency,
            merchant=merchant,
            balance_after=balance_after,
        )

        if sent:
            logger.info(f"[OTP_TX_NOTIFY] Notification sent to {masked_phone}")
            return {"status": "sent", "phone": masked_phone, "tx_type": tx_type}
        else:
            logger.warning(f"[OTP_TX_NOTIFY] Failed to send notification to {masked_phone}")
            return {"status": "failed", "phone": masked_phone}

    except Exception as e:
        logger.error(f"[OTP_TX_NOTIFY] Error sending notification to {masked_phone}: {e}")
        raise self.retry(exc=e)
