"""Finance AI Service for EasyCard OTP Bot."""

import logging
from typing import Dict, List, Optional

import requests
from django.conf import settings

from .prompt_service import build_system_prompt, get_error_message

logger = logging.getLogger(__name__)


def get_easycard_user_context(phone_number: str) -> str:
    """Get EasyCard user financial context for AI.

    Args:
        phone_number: User's phone number

    Returns:
        Formatted string with user's financial data, or empty string if unavailable.
    """
    try:
        from easycard_integration.services import EasyCardDataService

        data = EasyCardDataService.get_user_financial_data(phone_number)
        if data.is_registered:
            return data.to_ai_context()
        return ""
    except ImportError:
        logger.debug("[AI_SERVICE] easycard_integration not available")
        return ""
    except Exception as e:
        logger.warning(f"[AI_SERVICE] Error getting EasyCard context: {e}")
        return ""


class FinanceAIServiceError(Exception):
    """AI Service error."""

    pass


class FinanceAIService:
    """AI Service for EasyCard finance questions.

    Uses OpenAI proxy for generating responses with EasyCard-specific prompts.
    """

    def __init__(self):
        self.proxy_url = getattr(
            settings,
            "AI_ASSISTANT_URL",
            "http://161.35.153.151:8080"
        )
        self.model = getattr(settings, "OTP_BOT_AI_MODEL", "gpt-4o-mini")
        self.max_tokens = getattr(settings, "OTP_BOT_AI_MAX_TOKENS", 500)
        self.temperature = getattr(settings, "OTP_BOT_AI_TEMPERATURE", 0.7)

    def get_response(
        self,
        phone_number: str,
        question: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        voice_mode: bool = False,
    ) -> str:
        """Get AI response for a finance question.

        Args:
            phone_number: User's phone number (for logging and EasyCard lookup)
            question: User's question
            chat_history: Previous messages for context
            voice_mode: If True, use shorter response for TTS

        Returns:
            AI response text
        """
        masked_phone = self._mask_phone(phone_number)
        logger.info(f"[AI_SERVICE] Request from {masked_phone}: {question[:50]}...")

        # Get system prompt from settings or fallback defaults
        system_prompt = build_system_prompt(voice_mode=voice_mode)

        # Get EasyCard user context (balance, cards, transactions)
        easycard_context = get_easycard_user_context(phone_number)
        if easycard_context:
            system_prompt = f"{system_prompt}\n\n{easycard_context}"
            logger.debug(f"[AI_SERVICE] Added EasyCard context for {masked_phone}")

        # Adjust max_tokens for voice mode (shorter responses)
        max_tokens = 200 if voice_mode else self.max_tokens

        try:
            response = requests.post(
                f"{self.proxy_url}/bot/openai-proxy/",
                json={
                    "system_prompt": system_prompt,
                    "question": question,
                    "chat_history": chat_history or [],
                    "model": self.model,
                    "max_tokens": max_tokens,
                    "temperature": self.temperature,
                },
                timeout=30,
            )

            result = response.json()

            if "answer" in result:
                answer = result["answer"]
                logger.info(f"[AI_SERVICE] Response for {masked_phone}: {len(answer)} chars")
                return answer
            elif "error" in result:
                logger.error(f"[AI_SERVICE] Proxy error: {result['error']}")
                return self._get_error_message("ai_error")
            else:
                logger.error(f"[AI_SERVICE] Unexpected response: {result}")
                return self._get_error_message("ai_error")

        except requests.exceptions.Timeout:
            logger.error(f"[AI_SERVICE] Timeout for {masked_phone}")
            return self._get_error_message("timeout")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"[AI_SERVICE] Connection error: {e}")
            return self._get_error_message("connection")
        except Exception as e:
            logger.error(f"[AI_SERVICE] Error: {e}", exc_info=True)
            return self._get_error_message("ai_error")

    def _mask_phone(self, phone_number: str) -> str:
        """Mask phone number for logging."""
        if len(phone_number) > 7:
            return phone_number[:7] + "***"
        return phone_number

    def _get_error_message(self, error_type: str) -> str:
        """Get user-friendly error message from settings or defaults."""
        return get_error_message(error_type)
