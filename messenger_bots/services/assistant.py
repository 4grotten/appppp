import logging
from typing import Dict, List, Optional

import requests
from django.conf import settings
from django.db import models
from organizations.models import Assistant, Organization
from shop.services.comment_services import CommentService

logger = logging.getLogger(__name__)

# Number of previous messages to include for context
CHAT_HISTORY_LIMIT = 5


class BotAssistantService:
    """Service for getting AI responses from the AI Assistant service."""

    @classmethod
    def get_response(
        cls,
        organization: Organization,
        question: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        user_language: Optional[str] = None,
    ) -> str:
        """
        Get AI response for a question using organization's assistant.
        Calls the AI Assistant service API.

        Args:
            organization: The organization
            question: User's question
            chat_history: List of previous messages [{"role": "user/assistant", "content": "..."}]
            user_language: User's language code (e.g., "ru", "en", "kg")
        """
        logger.info("[AI_ASSISTANT] ====== GET RESPONSE ======")
        logger.info(
            f"[AI_ASSISTANT] org_id={organization.id}, org='{organization.title}'"
        )
        logger.info(
            f"[AI_ASSISTANT] question='{question[:100]}', language={user_language}"
        )
        logger.debug(
            f"[AI_ASSISTANT] chat_history={len(chat_history) if chat_history else 0} messages"
        )

        try:
            # Check if organization has an active assistant
            assistant = getattr(organization, "assistant", None)
            if not assistant:
                logger.error(
                    f"[AI_ASSISTANT] ERROR: No assistant configured for org {organization.id}"
                )
                return cls._get_message("assistant_not_active", user_language)

            if not assistant.is_enabled:
                logger.error(
                    f"[AI_ASSISTANT] ERROR: Assistant '{assistant.name}' is disabled"
                )
                return cls._get_message("assistant_not_active", user_language)

            logger.info(
                f"[AI_ASSISTANT] Assistant: '{assistant.name}', enabled={assistant.is_enabled}"
            )

            # Prepare training data
            logger.debug("[AI_ASSISTANT] Preparing training data...")
            training_data = cls._prepare_training_data(
                organization, assistant, user_language
            )
            logger.debug("[AI_ASSISTANT] Training data prepared")

            # Call AI Assistant service with chat history
            logger.info("[AI_ASSISTANT] Calling AI service...")
            response = cls._call_ai_service(
                question, training_data, chat_history, user_language
            )
            logger.info(f"[AI_ASSISTANT] Response received: '{response[:100]}...'")
            logger.info("[AI_ASSISTANT] ====== GET RESPONSE END ======")
            return response

        except Exception as e:
            logger.error(
                f"[AI_ASSISTANT] EXCEPTION in get_response: {e}", exc_info=True
            )
            return cls._get_message("error", user_language)

    @classmethod
    def _prepare_training_data(
        cls,
        organization: Organization,
        assistant: Assistant,
        user_language: Optional[str] = None,
    ) -> dict:
        """Prepare training data for the AI assistant - same as website chat."""
        # Use the same training data as website chat
        training_data = CommentService.get_training_data(assistant=assistant)

        # Add organization page URL (same as website chat)
        site_url = getattr(settings, "SITE_URL", "https://apofiz.com")
        training_data["organization_page_url"] = f"{site_url}/org/{organization.id}"

        # Add organization_info with contacts (required by ai_assistant prompts)
        phones = list(
            organization.phone_numbers.values_list("phone_number", flat=True)
        )
        social_links = ", ".join(
            organization.social_contacts.values_list("url", flat=True)
        )
        training_data["organization_info"] = {
            "phones": phones,
            "address": organization.address or "",
            "opens_at": str(organization.opens_at) if organization.opens_at else "",
            "closes_at": str(organization.closes_at) if organization.closes_at else "",
            "social_links": social_links,
        }

        # Add marketing_info from active coupons/promotions
        training_data["marketing_info"] = cls._get_marketing_info(organization)

        # Add language instruction if provided
        if user_language:
            training_data["assistant_info"]["response_language"] = cls._get_language_name(user_language)

        return training_data

    @classmethod
    def _get_marketing_info(cls, organization: Organization) -> List[str]:
        """
        Get marketing info (promotions, discounts, coupons) for AI prompt.
        Returns list of strings describing active promotions.
        """
        from django.utils import timezone
        from organizations.models import Coupon, DiscountCard

        marketing = []

        try:
            # Get active coupons with descriptions
            now = timezone.now()
            coupons = Coupon.objects.filter(
                organization=organization,
                is_active=True,
            ).filter(
                # Not expired or always active
                models.Q(expire_date__isnull=True) |
                models.Q(expire_date__gt=now) |
                models.Q(always_active=True)
            )

            for coupon in coupons:
                if coupon.description:
                    if coupon.percent:
                        marketing.append(f"{coupon.description} (-{coupon.percent}%)")
                    else:
                        marketing.append(coupon.description)
                elif coupon.percent:
                    if coupon.coupon_type == Coupon.DISCOUNT:
                        marketing.append(f"Скидка {coupon.percent}%")
                    elif coupon.product:
                        marketing.append(f"Скидка {coupon.percent}% на {coupon.product.name}")

            # Get discount cards info
            discount_cards = DiscountCard.objects.filter(
                organization=organization,
                is_published=True,
            ).order_by("percent")[:3]

            for card in discount_cards:
                if card.type == DiscountCard.FIXED:
                    marketing.append(f"Скидочная карта: {card.percent}%")
                elif card.type == DiscountCard.CASHBACK:
                    marketing.append(f"Кешбэк: {card.percent}%")
                elif card.type == DiscountCard.CUMULATIVE:
                    marketing.append(f"Накопительная скидка до {card.percent}%")

        except Exception as e:
            logger.warning(f"Error getting marketing info: {e}")

        return marketing

    @classmethod
    def _get_items_info(cls, organization: Organization) -> str:
        try:
            from shop.models import ShopItem

            items = (
                ShopItem.objects.filter(
                    organization=organization,
                    is_published=True,
                    removed_at__isnull=True,
                )
                .select_related("subcategory")
                .only("id", "name", "description", "price", "subcategory__name")[:50]
            )

            if not items:
                return "Нет доступных товаров/услуг."

            site_url = getattr(settings, "SITE_URL", "https://apofiz.com")

            items_list = []
            for item in items:
                item_str = f"- {item.name}"
                if item.price:
                    item_str += f" ({item.price} {organization.currency_id})"
                # Add product URL
                item_str += f" | Ссылка: {site_url}/p/{item.id}"
                if item.description:
                    # Truncate long descriptions
                    desc = (
                        item.description[:100] + "..."
                        if len(item.description) > 100
                        else item.description
                    )
                    item_str += f" | {desc}"
                items_list.append(item_str)

            return "\n".join(items_list)

        except Exception as e:
            logger.error(f"Error getting items info: {e}")
            return ""

    @classmethod
    def _get_qa_pairs(cls, assistant: Assistant) -> List[Dict]:
        try:
            from organizations.models import Answer

            answers = (
                Answer.objects.filter(assistant=assistant)
                .select_related("question")
                .prefetch_related("files")
            )

            qa_list = []
            for answer in answers:
                # Get file URLs
                file_urls = []
                for answer_file in answer.files.all():
                    if answer_file.file:
                        file_urls.append(answer_file.file.url)

                qa_list.append(
                    {
                        "question": answer.question.text if answer.question else "",
                        "answer": answer.text,
                        "files": file_urls,
                    }
                )

            return qa_list

        except Exception as e:
            logger.error(f"Error getting Q&A pairs: {e}")
            return []

    @classmethod
    def _get_catalog_file_url(cls, organization: Organization) -> Optional[str]:
        try:
            from shop.services.assistant_data_service import AssistantDataService

            catalog_url = AssistantDataService.get_file_url(organization)
            if catalog_url:
                logger.debug(f"Found catalog file: {catalog_url}")
            return catalog_url

        except Exception as e:
            logger.error(f"Error getting catalog file URL: {e}")
            return None

    @classmethod
    def _load_file_content(cls, file_url: str) -> str:
        try:
            response = requests.get(file_url, timeout=15)
            response.raise_for_status()
            content = response.content
            file_url_lower = file_url.lower()

            if file_url_lower.endswith(".pdf"):
                import io

                try:
                    import PyPDF2

                    pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text() or ""
                    return text.strip()
                except Exception as e:
                    logger.warning(f"PyPDF2 failed: {e}, trying pdfplumber")
                    try:
                        import pdfplumber

                        with pdfplumber.open(io.BytesIO(content)) as pdf:
                            text = ""
                            for page in pdf.pages:
                                text += page.extract_text() or ""
                            return text.strip()
                    except Exception:
                        return ""

            elif file_url_lower.endswith(".docx"):
                import io

                try:
                    import docx

                    doc = docx.Document(io.BytesIO(content))
                    return "\n".join([p.text for p in doc.paragraphs]).strip()
                except Exception:
                    return ""

            elif file_url_lower.endswith(".json"):
                import json

                data = json.loads(content.decode("utf-8"))
                if isinstance(data, list):
                    lines = []
                    for item in data[:50]:
                        name = item.get("name", "")
                        price = item.get("price", "")
                        url = item.get("url", "")
                        lines.append(f"- {name} ({price}) | {url}")
                    return "\n".join(lines)
                return str(data)[:2000]

            elif file_url_lower.endswith((".txt", ".csv", ".md")):
                return content.decode("utf-8").strip()[:5000]

            return ""

        except Exception as e:
            logger.error(f"Error loading file {file_url}: {e}")
            return ""

    @classmethod
    def _call_ai_service(
        cls,
        question: str,
        training_data: dict,
        chat_history: Optional[List[Dict[str, str]]] = None,
        user_language: Optional[str] = None,
    ) -> str:
        """
        Call AI service to get response.

        Uses direct OpenAI API with our custom prompts for consistent formatting
        (product links, ###NEXT### separators for pagination, etc.)
        """
        logger.info("[AI_ASSISTANT] _call_ai_service: Using direct OpenAI API")
        return cls._fallback_openai_response(
            question, training_data, chat_history, user_language
        )

    @classmethod
    def _fallback_openai_response(
        cls,
        question: str,
        training_data: dict,
        chat_history: Optional[List[Dict[str, str]]] = None,
        user_language: Optional[str] = None,
    ) -> str:
        """
        Fallback to direct OpenAI call if AI service is unavailable.

        Uses ai_utils for consistent prompts and file handling,
        ensuring compatibility with telegram.py's product parsing.
        """
        from messenger_bots.services.ai_utils import (
            build_system_prompt,
            call_openai,
        )

        logger.info(
            "[AI_ASSISTANT] _fallback_openai_response: Using OpenAI API directly"
        )
        try:
            api_key = getattr(settings, "OPENAI_API_KEY", None)
            if not api_key:
                logger.error("[AI_ASSISTANT] ERROR: OPENAI_API_KEY not configured!")
                return cls._get_message("service_unavailable", user_language)
            logger.debug(f"[AI_ASSISTANT] OpenAI API key found: {api_key[:10]}...")

            assistant_info = training_data.get("assistant_info", {})
            organization_info = training_data.get("organization_info", {})
            organization_page_url = training_data.get(
                "organization_page_url", "https://apofiz.com"
            )
            qa_pairs = training_data.get("answers", [])

            # Debug Q&A data
            print(f"[AI_ASSISTANT] Q&A pairs count: {len(qa_pairs)}")
            if qa_pairs:
                for i, qa in enumerate(qa_pairs):
                    q_text = (qa.get('question') or '')[:50]
                    a_text = (qa.get('answer') or '')[:50]
                    files_count = len(qa.get('files') or [])
                    print(f"[AI_ASSISTANT] Q&A {i+1}: Q='{q_text}' A='{a_text}' files={files_count}")
            marketing_info = training_data.get("marketing_info", [])
            item_info = training_data.get("item_info")

            # Load full catalog (same as website chat - no filtering)
            catalog_content = ""
            catalog_file = training_data.get("catalog_file")

            from messenger_bots.services.ai_utils import (
                format_catalog_json,
                get_http_session_with_retry,
            )

            if catalog_file:
                print(f"[AI_ASSISTANT] Loading catalog from: {catalog_file}")
                try:
                    session = get_http_session_with_retry()
                    response = session.get(catalog_file, timeout=(5, 15))
                    response.raise_for_status()
                    catalog_content = format_catalog_json(response.content)

                    print(f"[AI_ASSISTANT] catalog loaded: {len(catalog_content)} chars")
                except Exception as e:
                    print(f"[AI_ASSISTANT] ERROR loading catalog {catalog_file}: {e}")

            # Build comprehensive system prompt (compatible with telegram.py parsing)
            system_prompt = build_system_prompt(
                assistant_info=assistant_info,
                organization_info=organization_info,
                organization_page_url=organization_page_url,
                qa_pairs=qa_pairs,
                catalog_content=catalog_content,
                marketing_info=marketing_info,
                item_info=item_info or {},
                user_language=user_language or "ru",
            )

            # Call OpenAI API
            answer = call_openai(
                question=question,
                system_prompt=system_prompt,
                chat_history=chat_history,
                model="gpt-4o-mini",  # 128k context, cheaper than gpt-3.5-turbo
                max_tokens=1500,
            )

            if answer:
                print(f"[AI_ASSISTANT] OpenAI response length: {len(answer)} chars")
                print(f"[AI_ASSISTANT] Full answer:\n{answer}")
                logger.info(
                    f"[AI_ASSISTANT] OpenAI fallback SUCCESS: answer='{answer[:80]}...'"
                )
                return answer
            else:
                return cls._get_message("error", user_language)

        except Exception as e:
            logger.error(
                f"[AI_ASSISTANT] ERROR: OpenAI fallback failed: {e}", exc_info=True
            )
            return cls._get_message("error", user_language)

    # ============== Multilanguage Support ==============

    # Supported languages (Russian and English only for now)
    SUPPORTED_LANGUAGES = {
        "ru": "Русский",
        "en": "English",
    }

    # Messages in different languages
    MESSAGES = {
        "assistant_not_active": {
            "ru": "К сожалению, AI-ассистент для этой организации не активен.",
            "en": "Unfortunately, the AI assistant for this organization is not active.",
        },
        "error": {
            "ru": "Извините, произошла ошибка при обработке вашего запроса. Попробуйте позже.",
            "en": "Sorry, an error occurred while processing your request. Please try again later.",
        },
        "timeout": {
            "ru": "Извините, сервис не отвечает. Попробуйте позже.",
            "en": "Sorry, the service is not responding. Please try again later.",
        },
        "no_response": {
            "ru": "Не удалось получить ответ.",
            "en": "Could not get a response.",
        },
        "service_unavailable": {
            "ru": "Сервис временно недоступен. Попробуйте позже.",
            "en": "Service temporarily unavailable. Please try again later.",
        },
        "welcome": {
            "ru": "Здравствуйте! Чем могу помочь?",
            "en": "Hello! How can I help you?",
        },
        "catalog_button": {
            "ru": "Каталог товаров",
            "en": "Product Catalog",
        },
        "contacts_button": {
            "ru": "Адрес и контакты",
            "en": "Address & Contacts",
        },
        "no_products": {
            "ru": "К сожалению, товары не найдены.",
            "en": "Unfortunately, no products were found.",
        },
    }

    @classmethod
    def _get_message(cls, key: str, language: Optional[str] = None) -> str:
        """Get a message in the specified language."""
        lang = language if language in cls.SUPPORTED_LANGUAGES else "ru"
        messages = cls.MESSAGES.get(key, {})
        return messages.get(lang, messages.get("ru", ""))

    @classmethod
    def _get_language_name(cls, code: str) -> str:
        """Get language name by code."""
        return cls.SUPPORTED_LANGUAGES.get(code, "Русский")

    @classmethod
    def detect_language_from_telegram(cls, user: dict) -> str:
        """Detect user language from Telegram user data."""
        lang_code = user.get("language_code", "ru")

        # Get first 2 chars of language code
        short_code = lang_code[:2] if lang_code else "ru"

        # Only support ru and en for now
        return short_code if short_code in cls.SUPPORTED_LANGUAGES else "ru"
