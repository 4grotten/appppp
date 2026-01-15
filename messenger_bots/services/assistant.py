import logging
import requests
from typing import Optional, List, Dict
from django.conf import settings

from organizations.models import Organization, Assistant

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
        logger.info(f"[AI_ASSISTANT] ====== GET RESPONSE ======")
        logger.info(f"[AI_ASSISTANT] org_id={organization.id}, org='{organization.title}'")
        logger.info(f"[AI_ASSISTANT] question='{question[:100]}', language={user_language}")
        logger.debug(f"[AI_ASSISTANT] chat_history={len(chat_history) if chat_history else 0} messages")

        try:
            # Check if organization has an active assistant
            assistant = getattr(organization, "assistant", None)
            if not assistant:
                logger.error(f"[AI_ASSISTANT] ERROR: No assistant configured for org {organization.id}")
                return cls._get_message("assistant_not_active", user_language)

            if not assistant.is_enabled:
                logger.error(f"[AI_ASSISTANT] ERROR: Assistant '{assistant.name}' is disabled")
                return cls._get_message("assistant_not_active", user_language)

            logger.info(f"[AI_ASSISTANT] Assistant: '{assistant.name}', enabled={assistant.is_enabled}")

            # Prepare training data
            logger.debug(f"[AI_ASSISTANT] Preparing training data...")
            training_data = cls._prepare_training_data(organization, assistant, user_language)
            logger.debug(f"[AI_ASSISTANT] Training data prepared")

            # Call AI Assistant service with chat history
            logger.info(f"[AI_ASSISTANT] Calling AI service...")
            response = cls._call_ai_service(question, training_data, chat_history, user_language)
            logger.info(f"[AI_ASSISTANT] Response received: '{response[:100]}...'")
            logger.info(f"[AI_ASSISTANT] ====== GET RESPONSE END ======")
            return response

        except Exception as e:
            logger.error(f"[AI_ASSISTANT] EXCEPTION in get_response: {e}", exc_info=True)
            return cls._get_message("error", user_language)

    @classmethod
    def _prepare_training_data(
        cls,
        organization: Organization,
        assistant: Assistant,
        user_language: Optional[str] = None,
    ) -> dict:
        """Prepare training data for the AI assistant."""
        # Get organization info
        organization_info = {
            "name": organization.title,
            "description": organization.description or "",
            "address": organization.address or "",
            "opens_at": str(organization.opens_at) if organization.opens_at else "",
            "closes_at": str(organization.closes_at) if organization.closes_at else "",
        }

        # Get phone numbers
        phone_numbers = list(organization.phone_numbers.values_list("phone_number", flat=True))
        if phone_numbers:
            organization_info["phones"] = ", ".join(phone_numbers)

        # Get social contacts
        social_contacts = list(organization.social_contacts.values_list("url", flat=True))
        if social_contacts:
            organization_info["social_links"] = ", ".join(social_contacts)

        items_info = cls._get_items_info(organization)

        # Prepare assistant info
        assistant_info = {
            "name": assistant.name,
            "gender": assistant.get_gender_display() if hasattr(assistant, "get_gender_display") else assistant.gender,
            "position": assistant.position,
            "organization": organization.title,
        }

        # Add language instruction if provided
        if user_language:
            assistant_info["response_language"] = cls._get_language_name(user_language)

        # Get Q&A training pairs (like website does)
        answers = cls._get_qa_pairs(assistant)

        # Get catalog file URL
        catalog_file = cls._get_catalog_file_url(organization)
        org_url = f"{settings.SITE_URL}/organizations/{assistant.organization.id}"

        return {
            "assistant_info": assistant_info,
            "organization_info": organization_info,
            "item_info": items_info,
            "answers": answers,
            "catalog_file": catalog_file,
            "organization_page_url": org_url,
        }

    @classmethod
    def _get_items_info(cls, organization: Organization) -> str:
        """Get formatted items/products info for context."""
        try:
            from shop.models import ShopItem

            items = ShopItem.objects.filter(
                organization=organization,
                is_published=True,
                removed_at__isnull=True,
            ).select_related("subcategory").only(
                "id", "name", "description", "price", "subcategory__name"
            )[:50]

            if not items:
                return "Нет доступных товаров/услуг."

            # Get site URL for constructing item links
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
                    desc = item.description[:100] + "..." if len(item.description) > 100 else item.description
                    item_str += f" | {desc}"
                items_list.append(item_str)

            return "\n".join(items_list)

        except Exception as e:
            logger.error(f"Error getting items info: {e}")
            return ""

    @classmethod
    def _get_qa_pairs(cls, assistant: Assistant) -> List[Dict]:
        """Get Q&A training pairs for the assistant (like website does)."""
        try:
            from organizations.models import Answer

            answers = Answer.objects.filter(
                assistant=assistant
            ).select_related("question").prefetch_related("files")

            qa_list = []
            for answer in answers:
                # Get file URLs
                file_urls = []
                for answer_file in answer.files.all():
                    if answer_file.file:
                        file_urls.append(answer_file.file.url)

                qa_list.append({
                    "question": answer.question.text if answer.question else "",
                    "answer": answer.text,
                    "files": file_urls,
                })

            return qa_list

        except Exception as e:
            logger.error(f"Error getting Q&A pairs: {e}")
            return []

    @classmethod
    def _get_catalog_file_url(cls, organization: Organization) -> Optional[str]:
        """Get catalog JSON file URL for the organization."""
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
        """Load and extract text content from a file URL (PDF, DOCX, JSON, TXT)."""
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
        """Call the AI Assistant service API."""
        ai_service_url = getattr(settings, "AI_ASSISTANT_URL", "http://ai_assistant:8001")
        endpoint = f"{ai_service_url}/bot/comments/"

        logger.info(f"[AI_ASSISTANT] _call_ai_service: endpoint={endpoint}")
        logger.debug(f"[AI_ASSISTANT] AI_ASSISTANT_URL from settings: {ai_service_url}")

        try:
            logger.debug(f"[AI_ASSISTANT] Sending POST request to AI service...")
            response = requests.post(
                endpoint,
                json={
                    "question": question,
                    "training_data": training_data,
                    "chat_history": chat_history or [],
                },
                timeout=30,
            )
            logger.info(f"[AI_ASSISTANT] AI service response: status_code={response.status_code}")
            response.raise_for_status()

            data = response.json()
            answer = data.get("answer", cls._get_message("no_response", user_language))
            logger.info(f"[AI_ASSISTANT] AI service SUCCESS: answer='{answer[:80]}...'")
            return answer

        except requests.Timeout:
            logger.error(f"[AI_ASSISTANT] ERROR: AI service TIMEOUT (30s)")
            return cls._get_message("timeout", user_language)

        except requests.RequestException as e:
            logger.error(f"[AI_ASSISTANT] ERROR: AI service request failed: {e}")
            logger.info(f"[AI_ASSISTANT] Trying fallback to OpenAI...")
            # Fallback: try to use local OpenAI directly
            return cls._fallback_openai_response(question, training_data, chat_history, user_language)

    @classmethod
    def _fallback_openai_response(
        cls,
        question: str,
        training_data: dict,
        chat_history: Optional[List[Dict[str, str]]] = None,
        user_language: Optional[str] = None,
    ) -> str:
        """Fallback to direct OpenAI call if AI service is unavailable."""
        logger.info(f"[AI_ASSISTANT] _fallback_openai_response: Using OpenAI API directly")
        try:
            api_key = getattr(settings, "OPENAI_API_KEY", None)
            if not api_key:
                logger.error(f"[AI_ASSISTANT] ERROR: OPENAI_API_KEY not configured!")
                return cls._get_message("service_unavailable", user_language)
            logger.debug(f"[AI_ASSISTANT] OpenAI API key found: {api_key[:10]}...")

            assistant_info = training_data.get("assistant_info", {})
            organization_info = training_data.get("organization_info", {})
            item_info = training_data.get("item_info", "")
            answers = training_data.get("answers", [])

            # Build language instruction
            language_instruction = ""
            if user_language:
                lang_name = cls._get_language_name(user_language)
                language_instruction = f"\nВАЖНО: Отвечай на языке: {lang_name}."

            # Build Q&A training section with files
            qa_section = ""
            if answers:
                qa_section = "\n\nПримеры вопросов и ответов:\n"
                for qa in answers:
                    qa_section += f"В: {qa.get('question', '')}\nО: {qa.get('answer', '')}\n"
                    # Load file content (like AI service does)
                    for file_url in qa.get("files", []):
                        if file_url:
                            try:
                                file_content = cls._load_file_content(file_url)
                                if file_content:
                                    qa_section += f"Содержимое файла: {file_content}\n"
                            except Exception as e:
                                logger.warning(f"Failed to load file {file_url}: {e}")

            catalog_section = ""
            catalog_file = training_data.get("catalog_file")
            if catalog_file:
                try:
                    catalog_content = cls._load_file_content(catalog_file)
                    if catalog_content:
                        catalog_section = f"\n\n=== КАТАЛОГ ТОВАРОВ ===\n{catalog_content}\n"
                except Exception as e:
                    logger.warning(f"Failed to load catalog {catalog_file}: {e}")

            system_prompt = f"""Ты полезный ассистент по имени {assistant_info.get('name', 'Ассистент')},
работающий в организации {assistant_info.get('organization', 'неизвестная организация')}.
Твоя должность: {assistant_info.get('position', 'консультант')}.

Информация об организации:
{organization_info}
{qa_section}
Доступные товары/услуги:
{item_info}
{catalog_section}
Отвечай кратко и по существу. Если не знаешь ответа, предложи связаться с организацией напрямую.{language_instruction}"""

            # Build messages array with chat history
            messages = [{"role": "system", "content": system_prompt}]

            # Add chat history (last N messages for context)
            if chat_history:
                for msg in chat_history[-CHAT_HISTORY_LIMIT:]:
                    messages.append({
                        "role": msg["role"],
                        "content": msg["content"],
                    })

            # Add current question
            messages.append({"role": "user", "content": question})

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            }
            payload = {
                "model": "gpt-4o-mini",
                "messages": messages,
                "max_tokens": 300,
            }

            logger.debug(f"[AI_ASSISTANT] Sending request to OpenAI API...")
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30,
            )
            logger.info(f"[AI_ASSISTANT] OpenAI API response: status_code={response.status_code}")
            response.raise_for_status()

            data = response.json()
            answer = data["choices"][0]["message"]["content"].strip()
            logger.info(f"[AI_ASSISTANT] OpenAI fallback SUCCESS: answer='{answer[:80]}...'")
            return answer

        except Exception as e:
            logger.error(f"[AI_ASSISTANT] ERROR: OpenAI fallback failed: {e}", exc_info=True)
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
