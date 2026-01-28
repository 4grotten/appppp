"""Celery tasks for OTP Bot service."""

import base64
import logging
from typing import Optional

from celery import shared_task
from django.utils import timezone

from .models import OTPCode, ChatSession

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
    from .services.waha_otp import WAHAOTPClient
    from .services.ai_service import FinanceAIService
    from .services.elevenlabs import ElevenLabsService

    masked_phone = f"+{phone[:7]}***" if len(phone) > 7 else f"+{phone}"
    logger.info(f"[OTP_VOICE_TASK] Processing voice from {masked_phone}")

    waha = WAHAOTPClient()
    ai = FinanceAIService()
    elevenlabs = ElevenLabsService()

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
    voice_mode: bool = False,
):
    """Process text message asynchronously (AI response + optional TTS).

    Offloaded from webhook handler for fast webhook response time.
    AI calls can take 1-5 seconds, which would block the webhook.

    Args:
        phone: User's phone number (without + prefix)
        text: User's message text
        voice_mode: Whether to respond with voice (TTS)
    """
    from .services.waha_otp import WAHAOTPClient
    from .services.ai_service import FinanceAIService
    from .services.elevenlabs import ElevenLabsService

    masked_phone = f"+{phone[:7]}***" if len(phone) > 7 else f"+{phone}"
    logger.info(f"[OTP_TEXT_TASK] Processing text from {masked_phone}: {text[:30]}...")

    waha = WAHAOTPClient()
    ai = FinanceAIService()
    elevenlabs = ElevenLabsService()

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
    """Download voice audio using multiple fallback methods.

    Tries in order:
    1. media.data (base64 in payload)
    2. media.url (pre-signed URL)
    3. mediaUrl (root level)
    4. WAHA download API with message_id
    5. WAHA download API with @c.us format
    6. WAHA download API with raw ID

    Args:
        phone: User's phone number
        message_id: WhatsApp message ID
        payload: Full webhook payload
        waha: WAHAOTPClient instance

    Returns:
        Audio bytes or None
    """
    from messenger_bots.services.whatsapp.http_client import waha_request

    audio_bytes = None
    masked_phone = f"+{phone[:7]}***" if len(phone) > 7 else f"+{phone}"

    # Method 1: media.data (base64)
    media_data = payload.get("media", {}).get("data")
    if media_data:
        try:
            audio_bytes = base64.b64decode(media_data)
            logger.info(f"[OTP_VOICE_TASK] Method 1 (base64): {len(audio_bytes)} bytes")
            return audio_bytes
        except Exception as e:
            logger.debug(f"[OTP_VOICE_TASK] Method 1 failed: {e}")

    # Method 2: media.url
    media_url = payload.get("media", {}).get("url")
    if media_url:
        try:
            resp = waha_request("GET", media_url, timeout=(5, 30))
            if resp.ok:
                audio_bytes = resp.content
                logger.info(f"[OTP_VOICE_TASK] Method 2 (media.url): {len(audio_bytes)} bytes")
                return audio_bytes
        except Exception as e:
            logger.debug(f"[OTP_VOICE_TASK] Method 2 failed: {e}")

    # Method 3: mediaUrl at root
    media_url_root = payload.get("mediaUrl")
    if media_url_root:
        try:
            resp = waha_request("GET", media_url_root, timeout=(5, 30))
            if resp.ok:
                audio_bytes = resp.content
                logger.info(f"[OTP_VOICE_TASK] Method 3 (mediaUrl): {len(audio_bytes)} bytes")
                return audio_bytes
        except Exception as e:
            logger.debug(f"[OTP_VOICE_TASK] Method 3 failed: {e}")

    # Method 4: WAHA download API
    audio_bytes = waha.download_media(message_id)
    if audio_bytes:
        logger.info(f"[OTP_VOICE_TASK] Method 4 (WAHA API): {len(audio_bytes)} bytes")
        return audio_bytes

    # Method 5: WAHA with @c.us format
    message_id_cus = message_id.replace("@s.whatsapp.net", "@c.us")
    if message_id_cus != message_id:
        audio_bytes = waha.download_media(message_id_cus)
        if audio_bytes:
            logger.info(f"[OTP_VOICE_TASK] Method 5 (@c.us): {len(audio_bytes)} bytes")
            return audio_bytes

    # Method 6: Raw message ID
    parts = message_id.split("_")
    if len(parts) >= 3:
        raw_id = parts[-1]
        audio_bytes = waha.download_media(raw_id)
        if audio_bytes:
            logger.info(f"[OTP_VOICE_TASK] Method 6 (raw ID): {len(audio_bytes)} bytes")
            return audio_bytes

    logger.error(f"[OTP_VOICE_TASK] All download methods failed for {masked_phone}")
    return None
