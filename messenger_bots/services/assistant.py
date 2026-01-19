import hashlib
import logging
import re
import time
from typing import Dict, List, Optional

import requests
from django.conf import settings
from django.core.cache import cache
from django.db import models
from organizations.models import Assistant, Organization
from shop.services.comment_services import CommentService

logger = logging.getLogger(__name__)

# Number of previous messages to include for context
CHAT_HISTORY_LIMIT = 5

# AI Response caching settings
RESPONSE_CACHE_TIMEOUT = 60 * 60  # 1 hour
FREQUENCY_CACHE_TIMEOUT = 24 * 60 * 60  # 24 hours

# Per-organization frequency threshold
MIN_FREQUENCY_TO_CACHE = 3  # Cache after 3 identical questions per org

# Global frequency threshold (across ALL organizations)
GLOBAL_MIN_FREQUENCY_TO_CACHE = 20  # Cache after 20 identical questions globally

# Common question patterns - cache immediately on first request
# These are normalized patterns (lowercase, no punctuation)
COMMON_QUESTION_PATTERNS = {
    # Greetings
    "привет", "здравствуйте", "добрый день", "добрый вечер", "доброе утро",
    "hello", "hi", "hey", "good morning", "good evening",
    # Contacts
    "контакты", "контакт", "телефон", "номер телефона", "позвонить",
    "адрес", "где находитесь", "где вы находитесь", "как доехать",
    "contacts", "contact", "phone", "address", "location",
    # Working hours
    "режим работы", "график работы", "время работы", "часы работы",
    "когда работаете", "во сколько открываетесь", "во сколько закрываетесь",
    "working hours", "open hours", "when do you open",
    # General info
    "что вы продаете", "чем занимаетесь", "о компании", "о магазине",
    "what do you sell", "about", "about company",
    # Delivery/Payment
    "доставка", "как заказать", "оплата", "способы оплаты",
    "delivery", "how to order", "payment",
}

# Metrics cache timeout
METRICS_CACHE_TIMEOUT = 24 * 60 * 60  # 24 hours

# Global frequency cache key
GLOBAL_FREQUENCY_CACHE_KEY = "ai_global_freq"


def normalize_question(question: str) -> str:
    """
    Normalize a question for cache key generation.
    - Lowercase
    - Remove extra whitespace
    - Remove punctuation (keep Cyrillic and Latin letters, numbers)
    """
    # Lowercase
    text = question.lower().strip()
    # Remove punctuation but keep letters (Cyrillic + Latin) and numbers
    text = re.sub(r'[^\w\sа-яёА-ЯЁ]', '', text)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def get_response_cache_key(org_id: int, question: str) -> str:
    """Generate cache key for AI response."""
    normalized = normalize_question(question)
    question_hash = hashlib.md5(normalized.encode()).hexdigest()[:12]
    return f"ai_response:{org_id}:{question_hash}"


def get_frequency_cache_key(org_id: int, question: str) -> str:
    """Generate cache key for question frequency tracking (per-org)."""
    normalized = normalize_question(question)
    question_hash = hashlib.md5(normalized.encode()).hexdigest()[:12]
    return f"ai_freq:{org_id}:{question_hash}"


def get_global_frequency(question: str) -> int:
    """Get global frequency count for a question (across all orgs)."""
    normalized = normalize_question(question)
    question_hash = hashlib.md5(normalized.encode()).hexdigest()[:12]
    cache_key = f"ai_global_freq:{question_hash}"
    return cache.get(cache_key) or 0


def increment_org_frequency(org_id: int, question: str) -> int:
    """
    Atomically increment and return per-org frequency count for a question.
    Uses cache.incr() for thread-safe operation with concurrent users.
    """
    normalized = normalize_question(question)
    question_hash = hashlib.md5(normalized.encode()).hexdigest()[:12]
    cache_key = f"ai_freq:{org_id}:{question_hash}"

    try:
        # Try atomic increment (works with Redis/Memcached)
        return cache.incr(cache_key)
    except ValueError:
        # Key doesn't exist, create it
        cache.set(cache_key, 1, timeout=FREQUENCY_CACHE_TIMEOUT)
        return 1


def increment_global_frequency(question: str) -> int:
    """
    Atomically increment and return global frequency count for a question.
    Uses cache.incr() for thread-safe operation with concurrent users.
    """
    normalized = normalize_question(question)
    question_hash = hashlib.md5(normalized.encode()).hexdigest()[:12]
    cache_key = f"ai_global_freq:{question_hash}"

    try:
        # Try atomic increment (works with Redis/Memcached)
        return cache.incr(cache_key)
    except ValueError:
        # Key doesn't exist, create it
        cache.set(cache_key, 1, timeout=FREQUENCY_CACHE_TIMEOUT)
        return 1


def is_common_question(question: str) -> bool:
    """Check if question matches common patterns that should be cached immediately."""
    normalized = normalize_question(question)
    # Exact match
    if normalized in COMMON_QUESTION_PATTERNS:
        return True
    # Check if normalized question starts with a common pattern
    for pattern in COMMON_QUESTION_PATTERNS:
        if normalized.startswith(pattern) or pattern in normalized:
            return True
    return False


def should_cache_response(question: str, org_frequency: int) -> bool:
    """
    Determine if a response should be cached based on:
    1. Common question patterns (cache immediately)
    2. Per-org frequency (>= 3)
    3. Global frequency (>= 20)
    """
    # Common patterns - always cache
    if is_common_question(question):
        logger.debug(f"[CACHE] Common pattern detected: '{question[:30]}...'")
        return True

    # Per-org frequency threshold
    if org_frequency >= MIN_FREQUENCY_TO_CACHE:
        logger.debug(f"[CACHE] Per-org frequency threshold met: {org_frequency}")
        return True

    # Global frequency threshold
    global_freq = get_global_frequency(question)
    if global_freq >= GLOBAL_MIN_FREQUENCY_TO_CACHE:
        logger.debug(f"[CACHE] Global frequency threshold met: {global_freq}")
        return True

    return False


def update_metrics(
    org_id: int,
    response_time_ms: float,
    cache_hit: bool,
    error: bool = False,
) -> None:
    """
    Update AI assistant metrics using atomic increments.
    Thread-safe for concurrent users.
    """
    try:
        org_key = str(org_id)
        base_key = f"ai_metrics:{org_key}"

        # Atomic increments for counters
        def safe_incr(key: str, delta: int = 1) -> int:
            try:
                return cache.incr(key, delta)
            except ValueError:
                cache.set(key, delta, timeout=METRICS_CACHE_TIMEOUT)
                return delta

        safe_incr(f"{base_key}:total_requests")
        safe_incr(f"{base_key}:total_response_time_ms", int(response_time_ms))

        if cache_hit:
            safe_incr(f"{base_key}:cache_hits")
        if error:
            safe_incr(f"{base_key}:errors")

        # Update timestamp (not critical if overwritten)
        cache.set(
            f"{base_key}:last_updated",
            time.strftime("%Y-%m-%d %H:%M:%S"),
            timeout=METRICS_CACHE_TIMEOUT
        )
    except Exception as e:
        logger.warning(f"[METRICS] Failed to update metrics: {e}")


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
        Uses smart caching for frequent questions.

        Args:
            organization: The organization
            question: User's question
            chat_history: List of previous messages [{"role": "user/assistant", "content": "..."}]
            user_language: User's language code (e.g., "ru", "en", "kg")
        """
        start_time = time.time()
        cache_hit = False
        error_occurred = False

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

            # Check response cache first (only for simple questions without much context)
            # Skip cache for questions with chat history (contextual questions)
            response_cache_key = get_response_cache_key(organization.id, question)
            if not chat_history or len(chat_history) <= 1:
                cached_response = cache.get(response_cache_key)
                if cached_response:
                    cache_hit = True
                    logger.info(f"[AI_ASSISTANT] CACHE HIT for question: '{question[:50]}...'")
                    response_time_ms = (time.time() - start_time) * 1000
                    update_metrics(organization.id, response_time_ms, cache_hit=True)
                    return cached_response

            # Track question frequency atomically (thread-safe for concurrent users)
            org_frequency = increment_org_frequency(organization.id, question)
            global_frequency = increment_global_frequency(question)

            logger.debug(
                f"[AI_ASSISTANT] Frequency - org: {org_frequency}, global: {global_frequency}"
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

            # Cache response based on frequency thresholds or common patterns
            # Don't cache product responses (contain prices that may change)
            is_product_response = "Товар:" in response or "Product:" in response
            if not is_product_response and should_cache_response(question, org_frequency):
                cache.set(response_cache_key, response, timeout=RESPONSE_CACHE_TIMEOUT)
                logger.info(
                    f"[AI_ASSISTANT] CACHED response (org_freq={org_frequency}, "
                    f"global_freq={global_frequency}, common={is_common_question(question)})"
                )

            logger.info("[AI_ASSISTANT] ====== GET RESPONSE END ======")
            return response

        except Exception as e:
            error_occurred = True
            logger.error(
                f"[AI_ASSISTANT] EXCEPTION in get_response: {e}", exc_info=True
            )
            return cls._get_message("error", user_language)

        finally:
            # Track metrics
            response_time_ms = (time.time() - start_time) * 1000
            update_metrics(
                organization.id,
                response_time_ms,
                cache_hit=cache_hit,
                error=error_occurred,
            )
            logger.info(f"[AI_ASSISTANT] Response time: {response_time_ms:.0f}ms")

    @classmethod
    def _prepare_training_data(
        cls,
        organization: Organization,
        assistant: Assistant,
        user_language: Optional[str] = None,
    ) -> dict:
        """
        Prepare training data for the AI assistant.
        Uses cached data if available (pre-cached by background task).
        """
        from django.core.cache import cache

        # Check cache first (populated by cache_assistant_training_data task)
        cache_key = f"assistant_training_data:{organization.id}"
        cached_data = cache.get(cache_key)

        if cached_data:
            logger.info(f"[AI_ASSISTANT] Using cached training data for org {organization.id}")
            training_data = cached_data
        else:
            logger.info(f"[AI_ASSISTANT] Cache miss, loading fresh data for org {organization.id}")
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

            # Use cached catalog if available, otherwise load fresh
            catalog_content = training_data.get("_cached_catalog", "")

            if catalog_content:
                print(f"[AI_ASSISTANT] Using cached catalog: {len(catalog_content)} chars")
            else:
                # Fallback: load catalog fresh if not cached
                catalog_file = training_data.get("catalog_file")
                if catalog_file:
                    from messenger_bots.services.ai_utils import (
                        format_catalog_json,
                        get_http_session_with_retry,
                    )
                    print(f"[AI_ASSISTANT] Cache miss, loading catalog from: {catalog_file}")
                    try:
                        session = get_http_session_with_retry()
                        response = session.get(catalog_file, timeout=(5, 15))
                        response.raise_for_status()
                        catalog_content = format_catalog_json(response.content)
                        print(f"[AI_ASSISTANT] catalog loaded: {len(catalog_content)} chars")
                    except Exception as e:
                        print(f"[AI_ASSISTANT] ERROR loading catalog {catalog_file}: {e}")

            # Get cached file contents if available
            cached_file_contents = training_data.get("_cached_file_contents", {})

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
                cached_file_contents=cached_file_contents,
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

    # Supported languages (Russian and English only)
    SUPPORTED_LANGUAGES = {
        "ru": "Русский",
        "en": "English",
    }

    # Messages in different languages (Russian and English only)
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
        "more_products": {
            "ru": "Показать ещё",
            "en": "Show more",
        },
    }

    @classmethod
    def _get_message(cls, key: str, language: Optional[str] = None) -> str:
        """Get a message in the specified language with fallback to ru/en."""
        messages = cls.MESSAGES.get(key, {})

        # Try exact language match
        if language and language in messages:
            return messages[language]

        # Fallback chain: ru -> en -> first available
        if "ru" in messages:
            return messages["ru"]
        if "en" in messages:
            return messages["en"]

        # Return first available or empty
        return next(iter(messages.values()), "")

    @classmethod
    def _get_language_name(cls, code: str) -> str:
        """Get language name by code."""
        return cls.SUPPORTED_LANGUAGES.get(code, "Русский")

    @classmethod
    def detect_language_from_telegram(cls, user: dict) -> str:
        """
        Detect user language from Telegram user data.
        Returns the language code (e.g., 'ru', 'en', 'kg').
        """
        lang_code = user.get("language_code", "ru")

        # Get first 2 chars of language code (e.g., "en-US" -> "en")
        short_code = lang_code[:2].lower() if lang_code else "ru"

        # Return the code if supported, otherwise default to 'ru'
        # But pass through unsupported codes too - AI can handle them
        if short_code in cls.SUPPORTED_LANGUAGES:
            return short_code

        # For unsupported but valid language codes, still pass them
        # The AI model can translate to most languages
        if len(short_code) == 2 and short_code.isalpha():
            return short_code

        return "ru"

    # ============== Metrics ==============

    @classmethod
    def get_metrics(cls, org_id: Optional[int] = None) -> dict:
        """
        Get AI assistant metrics.

        Args:
            org_id: If provided, get metrics for specific org. Otherwise, get all.

        Returns:
            Dict with metrics including:
            - total_requests: Total number of requests
            - cache_hits: Number of cache hits
            - cache_hit_rate: Percentage of cache hits
            - errors: Number of errors
            - avg_response_time_ms: Average response time in milliseconds
        """
        if org_id:
            # Read from atomic counter keys
            org_metrics = cls._read_org_metrics(org_id)
            return cls._calculate_rates(org_metrics)

        # For all orgs, we need to scan for metrics keys
        # This is a simplified implementation - returns empty for "all"
        # since atomic keys don't support easy enumeration
        logger.warning("[METRICS] get_metrics() without org_id not fully supported with atomic counters")
        return {}

    @classmethod
    def _read_org_metrics(cls, org_id: int) -> dict:
        """
        Read metrics for a specific organization from atomic counter keys.
        """
        base_key = f"ai_metrics:{org_id}"
        return {
            "total_requests": cache.get(f"{base_key}:total_requests") or 0,
            "cache_hits": cache.get(f"{base_key}:cache_hits") or 0,
            "errors": cache.get(f"{base_key}:errors") or 0,
            "total_response_time_ms": cache.get(f"{base_key}:total_response_time_ms") or 0,
            "last_updated": cache.get(f"{base_key}:last_updated"),
        }

    @classmethod
    def _calculate_rates(cls, metrics: dict) -> dict:
        """Calculate rate metrics from raw counts."""
        if not metrics:
            return {
                "total_requests": 0,
                "cache_hits": 0,
                "cache_hit_rate": 0.0,
                "errors": 0,
                "error_rate": 0.0,
                "avg_response_time_ms": 0.0,
                "last_updated": None,
            }

        total = metrics.get("total_requests", 0)
        hits = metrics.get("cache_hits", 0)
        errors = metrics.get("errors", 0)
        total_time = metrics.get("total_response_time_ms", 0)

        return {
            "total_requests": total,
            "cache_hits": hits,
            "cache_hit_rate": round((hits / total * 100) if total > 0 else 0, 1),
            "errors": errors,
            "error_rate": round((errors / total * 100) if total > 0 else 0, 1),
            "avg_response_time_ms": round(total_time / total if total > 0 else 0, 0),
            "last_updated": metrics.get("last_updated"),
        }

    @classmethod
    def clear_response_cache(cls, org_id: int) -> int:
        """
        Clear all cached AI responses for an organization.
        Useful when training data is updated.

        Returns number of keys cleared (approximate).
        """
        # Note: This is a simple implementation. For production with Redis,
        # you might want to use SCAN with pattern matching.
        logger.info(f"[AI_ASSISTANT] Clearing response cache for org {org_id}")
        # The training data cache invalidation already handles this via signals
        # This method is for manual clearing if needed
        return 0
