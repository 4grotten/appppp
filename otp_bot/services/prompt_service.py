"""Prompt settings service for OTP Bot with caching.

Loads AI prompt settings from database with 5-minute cache.
Falls back to hardcoded prompts in prompts.py if settings not active.
"""

import logging
from typing import Any, Dict, Optional

from django.core.cache import cache

logger = logging.getLogger(__name__)

# Cache configuration
OTP_PROMPT_CACHE_KEY = "otp_bot_prompt_settings"
OTP_PROMPT_CACHE_TIMEOUT = 300  # 5 minutes


def get_otp_prompt_settings() -> Dict[str, Any]:
    """Load OTP Bot prompt settings from database with caching.

    Returns:
        Dictionary with all prompt settings, or empty dict if not active/available.
    """
    cached = cache.get(OTP_PROMPT_CACHE_KEY)
    if cached is not None:
        return cached

    try:
        from ..models import OTPBotPromptSettings

        settings = OTPBotPromptSettings.objects.first()

        if not settings or not settings.is_active:
            logger.debug("[PROMPT_SERVICE] Settings not active, using defaults")
            cache.set(OTP_PROMPT_CACHE_KEY, {}, timeout=OTP_PROMPT_CACHE_TIMEOUT)
            return {}

        # Extract all fields except internal ones
        exclude_fields = {"id", "created_at", "updated_at"}
        data = {
            field.name: getattr(settings, field.name)
            for field in settings._meta.fields
            if field.name not in exclude_fields
        }

        cache.set(OTP_PROMPT_CACHE_KEY, data, timeout=OTP_PROMPT_CACHE_TIMEOUT)
        logger.debug("[PROMPT_SERVICE] Loaded settings from DB (is_active=True)")
        return data

    except Exception as e:
        logger.warning(f"[PROMPT_SERVICE] Error loading settings: {e}")
        cache.set(OTP_PROMPT_CACHE_KEY, {}, timeout=OTP_PROMPT_CACHE_TIMEOUT)
        return {}


def build_system_prompt(voice_mode: bool = False) -> str:
    """Build complete system prompt from settings or fallback to defaults.

    Args:
        voice_mode: If True, add voice-specific instructions for shorter responses.

    Returns:
        Complete system prompt string ready for AI API.
    """
    settings = get_otp_prompt_settings()

    # Fallback to hardcoded defaults
    if not settings:
        from ..prompts import get_system_prompt

        return get_system_prompt(voice_mode=voice_mode)

    # Build prompt from database settings
    parts = [
        settings.get("system_prompt_core", ""),
        f"\n## О Easy Card\n{settings.get('about_easycard', '')}",
        f"\n## Типы карт\n{settings.get('card_types', '')}",
        f"\n## Комиссии (в AED)\n### Единоразовые комиссии:\n{settings.get('fees_one_time', '')}",
        f"\n### Пополнение баланса:\n{settings.get('fees_topup', '')}",
        f"\n### Переводы:\n{settings.get('fees_transfer', '')}",
        f"\n### Транзакции:\n{settings.get('fees_transactions', '')}",
        f"\n## Курсы обмена\n{settings.get('exchange_rates', '')}",
        f"\n## Функции приложения\n{settings.get('app_features', '')}",
        f"\n## Важно\n{settings.get('important_notes', '')}",
        f"\n## Правила языка\n{settings.get('language_detection_rule', '')}",
        f"\n## Форматирование\n{settings.get('formatting_rules', '')}",
    ]

    # Add voice mode instructions
    if voice_mode:
        voice_max_words = settings.get("voice_max_words", 50)
        parts.append(
            f"\n## РЕЖИМ ГОЛОСОВОГО ОТВЕТА\n{settings.get('voice_mode_prompt', '')}\n"
            f"Максимум {voice_max_words} слов в ответе."
        )

    return "\n".join(part for part in parts if part.strip())


def get_error_message(error_type: str) -> str:
    """Get user-friendly error message from settings or defaults.

    Args:
        error_type: Type of error ('ai_error', 'timeout', 'voice_unavailable').

    Returns:
        Localized error message string.
    """
    settings = get_otp_prompt_settings()

    # Default messages (Russian)
    defaults = {
        "ai_error": "Извините, произошла ошибка. Попробуйте позже.",
        "timeout": "Сервис не отвечает. Попробуйте позже.",
        "connection": "Не удалось подключиться к сервису. Попробуйте позже.",
        "voice_unavailable": "Голосовые сообщения временно недоступны. Напишите текстом.",
    }

    if not settings:
        return defaults.get(error_type, defaults["ai_error"])

    # Map error types to settings fields
    field_map = {
        "ai_error": "error_ai",
        "timeout": "error_timeout",
        "connection": "error_ai",  # Use AI error for connection issues
        "voice_unavailable": "error_voice_unavailable",
    }

    field_name = field_map.get(error_type, "error_ai")
    return settings.get(field_name, defaults.get(error_type, defaults["ai_error"]))


def get_escalation_keywords() -> list:
    """Get list of keywords that trigger escalation to human operator.

    Returns:
        List of keywords (lowercase).
    """
    settings = get_otp_prompt_settings()

    if not settings:
        return ["оператор", "человек", "помощь", "живой"]

    keywords = settings.get("escalation_keywords", [])
    if isinstance(keywords, list):
        return [k.lower() for k in keywords if isinstance(k, str)]
    return []


def get_buttons_config() -> Dict[str, Any]:
    """Get WAHA Plus interactive buttons configuration.

    Returns:
        Dictionary with button configurations or empty dict.
    """
    settings = get_otp_prompt_settings()
    if not settings:
        return {}
    return settings.get("buttons_config", {})


def get_welcome_buttons() -> list:
    """Get welcome message buttons configuration.

    Returns:
        List of button configurations or empty list.
    """
    settings = get_otp_prompt_settings()
    if not settings:
        return []
    return settings.get("welcome_buttons", [])


def invalidate_cache() -> None:
    """Invalidate prompt settings cache.

    Called by signal when OTPBotPromptSettings is saved.
    """
    cache.delete(OTP_PROMPT_CACHE_KEY)
    logger.info("[PROMPT_SERVICE] Cache invalidated")


def get_easycard_exchange_rates_context() -> str:
    """Get current exchange rates from EasyCard database.

    Returns:
        Formatted string with exchange rates for AI context.
    """
    try:
        from easycard_integration.services import EasyCardDataService

        rates = EasyCardDataService.get_exchange_rates()
        if not rates:
            return ""

        parts = ["## Актуальные курсы обмена (из базы данных)"]
        for key, value in rates.items():
            # Format key for display
            key_display = key.replace("_", " ").upper()
            parts.append(f"- {key_display}: {value}")

        return "\n".join(parts)
    except ImportError:
        return ""
    except Exception:
        return ""


def get_easycard_fees_context() -> str:
    """Get current fees from EasyCard database.

    Returns:
        Formatted string with fees for AI context.
    """
    try:
        from easycard_integration.services import EasyCardDataService

        fees = EasyCardDataService.get_fees()
        if not fees:
            return ""

        parts = ["## Актуальные комиссии (из базы данных)"]
        for key, value in fees.items():
            # Format key for display
            key_display = key.replace("_", " ").title()
            parts.append(f"- {key_display}: {value} AED")

        return "\n".join(parts)
    except ImportError:
        return ""
    except Exception:
        return ""
