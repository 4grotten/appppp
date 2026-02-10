"""ElevenLabs STT/TTS Service for OTP Bot Voice Assistant.

Provides Speech-to-Text (STT) and Text-to-Speech (TTS) capabilities
using the ElevenLabs API.
"""

import logging
from typing import Optional

import requests
from django.conf import settings

from otp_bot.metrics import track_timing

logger = logging.getLogger(__name__)


class ElevenLabsError(Exception):
    """ElevenLabs API error."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class ElevenLabsService:
    """ElevenLabs Speech-to-Text and Text-to-Speech service.

    Configuration via Django settings:
    - ELEVENLABS_API_KEY: API key for authentication
    - ELEVENLABS_VOICE_ID: Voice ID for TTS (default: Laura)
    - ELEVENLABS_MODEL_TTS: TTS model (default: eleven_turbo_v2_5)
    - ELEVENLABS_MODEL_STT: STT model (default: scribe_v1)
    """

    BASE_URL = "https://api.elevenlabs.io"

    def __init__(self):
        self.api_key = getattr(settings, "ELEVENLABS_API_KEY", "")
        self.voice_id = getattr(
            settings,
            "ELEVENLABS_VOICE_ID",
            "FGY2WhTYpPnrIDTdsKH5",  # Laura voice
        )
        self.model_tts = getattr(
            settings,
            "ELEVENLABS_MODEL_TTS",
            "eleven_turbo_v2_5",
        )
        self.model_stt = getattr(
            settings,
            "ELEVENLABS_MODEL_STT",
            "scribe_v1",
        )

    def is_configured(self) -> bool:
        """Check if ElevenLabs API key is configured."""
        return bool(self.api_key)

    @track_timing("elevenlabs_stt")
    def speech_to_text(self, audio_bytes: bytes) -> Optional[str]:
        """Transcribe audio to text using ElevenLabs STT.

        Args:
            audio_bytes: Raw audio data (OGG/MP3/WAV supported)

        Returns:
            Transcribed text or None on error
        """
        if not self.api_key:
            logger.error("[ELEVENLABS] API key not configured")
            return None

        audio_size = len(audio_bytes)
        logger.info(f"[ELEVENLABS] STT: Processing {audio_size} bytes")

        try:
            response = requests.post(
                f"{self.BASE_URL}/v1/speech-to-text",
                headers={"xi-api-key": self.api_key},
                files={
                    "audio": ("voice.ogg", audio_bytes, "audio/ogg"),
                },
                data={"model_id": self.model_stt},
                timeout=30,
            )

            if response.status_code == 429:
                logger.warning("[ELEVENLABS] STT rate limit exceeded")
                return None

            if not response.ok:
                logger.error(
                    f"[ELEVENLABS] STT error: {response.status_code} {response.text[:200]}"
                )
                return None

            result = response.json()
            text = result.get("text", "").strip()

            if text:
                logger.info(f"[ELEVENLABS] STT result: {text[:50]}...")
            else:
                logger.warning("[ELEVENLABS] STT returned empty text")

            return text if text else None

        except requests.exceptions.Timeout:
            logger.error("[ELEVENLABS] STT timeout")
            return None
        except requests.exceptions.ConnectionError as e:
            logger.error(f"[ELEVENLABS] STT connection error: {e}")
            return None
        except Exception as e:
            logger.error(f"[ELEVENLABS] STT error: {e}", exc_info=True)
            return None

    @track_timing("elevenlabs_tts")
    def text_to_speech(self, text: str) -> Optional[bytes]:
        """Convert text to speech using ElevenLabs TTS.

        Args:
            text: Text to convert to speech (max ~5000 chars recommended)

        Returns:
            MP3 audio bytes or None on error
        """
        if not self.api_key:
            logger.error("[ELEVENLABS] API key not configured")
            return None

        if not text or not text.strip():
            logger.warning("[ELEVENLABS] TTS called with empty text")
            return None

        text = text.strip()
        logger.info(f"[ELEVENLABS] TTS: Converting {len(text)} chars")

        try:
            response = requests.post(
                f"{self.BASE_URL}/v1/text-to-speech/{self.voice_id}",
                headers={
                    "xi-api-key": self.api_key,
                    "Content-Type": "application/json",
                },
                params={"output_format": "mp3_44100_128"},
                json={
                    "text": text,
                    "model_id": self.model_tts,
                    "voice_settings": {
                        "stability": 0.5,
                        "similarity_boost": 0.75,
                        "style": 0.3,
                        "use_speaker_boost": True,
                    },
                },
                timeout=30,
            )

            if response.status_code == 429:
                logger.warning("[ELEVENLABS] TTS rate limit exceeded")
                return None

            if not response.ok:
                logger.error(
                    f"[ELEVENLABS] TTS error: {response.status_code} {response.text[:200]}"
                )
                return None

            audio_bytes = response.content

            if not audio_bytes:
                logger.error("[ELEVENLABS] TTS returned empty audio")
                return None

            logger.info(f"[ELEVENLABS] TTS result: {len(audio_bytes)} bytes")
            return audio_bytes

        except requests.exceptions.Timeout:
            logger.error("[ELEVENLABS] TTS timeout")
            return None
        except requests.exceptions.ConnectionError as e:
            logger.error(f"[ELEVENLABS] TTS connection error: {e}")
            return None
        except Exception as e:
            logger.error(f"[ELEVENLABS] TTS error: {e}", exc_info=True)
            return None
