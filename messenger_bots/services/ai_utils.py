"""
AI Assistant utilities for Telegram/WhatsApp bots.

This module consolidates functionality from the external ai_assistant service
to ensure compatibility with the Telegram bot's product parsing.
"""
import io
import json
import logging
from typing import Dict, List, Optional, Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from django.conf import settings

logger = logging.getLogger(__name__)


# ============== HTTP Session with Retry ==============

def get_http_session_with_retry(
    retries: int = 3,
    backoff_factor: float = 0.5,
    status_forcelist: tuple = (500, 502, 503, 504),
) -> requests.Session:
    """
    Create HTTP session with automatic retry on failures.

    Args:
        retries: Number of retry attempts
        backoff_factor: Delay multiplier between retries (0.5 = 0.5s, 1s, 2s...)
        status_forcelist: HTTP status codes to retry on

    Returns:
        Configured requests.Session with retry adapter
    """
    session = requests.Session()
    retry_strategy = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=["GET", "POST"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


# ============== File Reading Utilities ==============

def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF file content."""
    try:
        # Try pypdf first (newer library)
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(file_content))
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text.strip()
        except ImportError:
            pass

        # Fallback to PyPDF2
        try:
            import PyPDF2
            reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text.strip()
        except ImportError:
            pass

        # Fallback to pdfplumber
        try:
            import pdfplumber
            with pdfplumber.open(io.BytesIO(file_content)) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() or ""
                return text.strip()
        except ImportError:
            pass

        print("No PDF library available (pypdf, PyPDF2, or pdfplumber)")
        return ""

    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""


def extract_text_from_docx(file_content: bytes) -> str:
    """Extract text from DOCX file content."""
    try:
        try:
            from docx import Document
            doc = Document(io.BytesIO(file_content))
            return "\n".join([para.text for para in doc.paragraphs]).strip()
        except ImportError:
            pass

        try:
            import docx
            doc = docx.Document(io.BytesIO(file_content))
            return "\n".join([p.text for p in doc.paragraphs]).strip()
        except ImportError:
            pass

        print("No DOCX library available (python-docx)")
        return ""

    except Exception as e:
        print(f"Error extracting text from DOCX: {e}")
        return ""


def format_catalog_json(json_content) -> str:
    """Format catalog JSON into readable text for AI prompt."""
    try:
        if isinstance(json_content, bytes):
            json_content = json_content.decode('utf-8')

        items = json.loads(json_content)
        if not items:
            return "Catalog is empty."

        # Use neutral DATA: format to prevent AI from copying the format
        text = "FULL ORGANIZATION CATALOG:\n"
        text += "(Use scenario_B format with ###NEXT### separator when showing products!)\n\n"

        for item in items:
            name = item.get('name', 'Unknown Item')
            category = item.get('category', 'General')
            price = f"{item.get('price')} {item.get('currency', '')}" if item.get('price') else "Price not set"
            url = item.get('url', 'No link')

            # Use DATA: prefix - raw data, not response format
            text += f"DATA: name={name} | category={category} | price={price} | url={url}\n"

        return text

    except Exception as e:
        print(f"Error parsing catalog JSON: {e}")
        return ""


def read_file_from_url(file_url: str) -> str:
    """
    Read and extract text content from a file URL.
    Supports: PDF, DOCX, JSON, TXT, CSV, MD

    Uses HTTP session with automatic retry on server errors.
    """
    try:
        session = get_http_session_with_retry()
        response = session.get(file_url, timeout=(5, 15))  # (connect, read)
        response.raise_for_status()
        file_content = response.content

        # Extract file path without query parameters for extension check
        from urllib.parse import urlparse
        parsed_url = urlparse(file_url)
        file_path = parsed_url.path.lower()

        print(f"[READ_FILE] URL: {file_url[:100]}...")
        print(f"[READ_FILE] File path: {file_path}, size: {len(file_content)} bytes")

        if file_path.endswith(".pdf") or ".pdf" in file_url.lower():
            print("[READ_FILE] Detected PDF file")
            return extract_text_from_pdf(file_content)
        elif file_path.endswith(".docx") or ".docx" in file_url.lower():
            print("[READ_FILE] Detected DOCX file")
            return extract_text_from_docx(file_content)
        elif file_path.endswith(".json") or ".json" in file_url.lower():
            return format_catalog_json(file_content)
        elif file_path.endswith((".txt", ".csv", ".log", ".md")):
            try:
                return file_content.decode("utf-8")[:5000]
            except UnicodeDecodeError:
                print(f"Failed to decode file as UTF-8: {file_url}")
                return ""
        else:
            # Try to detect by content type or magic bytes
            print("[READ_FILE] Unknown extension, trying to detect type...")
            # PDF magic bytes: %PDF
            if file_content[:4] == b'%PDF':
                print("[READ_FILE] Detected PDF by magic bytes")
                return extract_text_from_pdf(file_content)
            # DOCX is a ZIP file starting with PK
            elif file_content[:2] == b'PK':
                print("[READ_FILE] Detected DOCX/ZIP by magic bytes")
                return extract_text_from_docx(file_content)
            else:
                print(f"[READ_FILE] Unsupported file type: {file_path}")
                return ""

    except requests.exceptions.RequestException as e:
        print(f"Error reading file from URL: {e}")
        return ""


# ============== Prompt Building ==============

def build_system_prompt(
    assistant_info: Dict[str, Any],
    organization_info: Dict[str, Any],
    organization_page_url: str,
    qa_pairs: List[Dict[str, Any]],
    catalog_content: str = "",
    marketing_info: List[str] = None,
    item_info: Dict[str, Any] = None,
    user_language: str = "ru",
    cached_file_contents: Dict[str, str] = None,
) -> str:
    """
    Build a comprehensive system prompt for the AI assistant.
    Structure copied from ai_assistant/bot/consumers.py for consistency.

    The product format is designed to be compatible with telegram.py's
    parse_products_from_response() function which expects:
    - "Товар:" or "Product:" at the start
    - "Ссылка:" or "Link:" with URL at the end
    """
    # ============== Language Detection (same as Web Chat) ==============
    # Map language code to full language name (only ru/en supported)
    LANGUAGE_MAP = {
        "ru": "Russian",
        "en": "English",
    }
    detected_lang = LANGUAGE_MAP.get(user_language, "Russian")

    # Language-specific instruction
    if user_language == "ru":
        lang_instruction = "Отвечай на Русском языке."
    elif user_language == "en":
        lang_instruction = "Answer strictly in ENGLISH. Translate all data from Russian to English."
    else:
        lang_instruction = f"Answer strictly in {detected_lang}. Translate all data to {detected_lang}."

    # Extract contact info
    phones = organization_info.get('phones', [])
    if isinstance(phones, list):
        phones_str = ", ".join([str(p) for p in phones])
    else:
        phones_str = str(phones)
    address_str = organization_info.get('address', 'Unknown')
    opens_at = organization_info.get('opens_at', 'Unknown')
    closes_at = organization_info.get('closes_at', 'Unknown')
    social_links = organization_info.get('social_links', '')

    # Marketing info
    marketing_str = ""
    if marketing_info:
        marketing_str = "\n".join([f"- {m}" for m in marketing_info])

    # Build prompt - SAME STRUCTURE AS consumers.py (Web Chat)
    prompt = (
        f"CRITICAL INSTRUCTION: USER LANGUAGE IS *** {detected_lang} ***.\n"
        f"{lang_instruction}\n"
        f"Even if the data below is in Russian, you MUST translate your final answer to {detected_lang}.\n\n"

        f"IDENTITY:\n"
        f"You are {assistant_info.get('name', 'Assistant')}, an assistant at {assistant_info.get('organization', 'organization')}.\n"
        f"Position: {assistant_info.get('position', 'consultant')}. Gender: {assistant_info.get('gender', 'not specified')}.\n\n"

        "⛔ STRICT FORMATTING RULES:\n"
        "1. NO MARKDOWN. No *, **, [text](url).\n"
        "2. Send LINKS as plain text only.\n"
        "3. SEPARATOR: Use '###NEXT###' to separate different products or the final link.\n\n"

        "🧠 LOGIC SCENARIOS:\n\n"

        "scenario_A: DISCOUNTS & COUPONS\n"
        "   - IF user asks about discounts, coupons, or bonuses:\n"
        "   - Answer ONLY about the promotions.\n"
        "   - DO NOT list products/items unless the user explicitly asks for them.\n"
        "   - DO NOT use the ###NEXT### tag in this scenario.\n"
        f"   - TRANSLATE the discounts info to {detected_lang} if needed.\n\n"

        "scenario_B: PRODUCTS (Catalogue)\n"
        "   ⚠️ CRITICAL: You MUST use this EXACT format for EACH product:\n"
        "   - DO NOT use dashes (-) or bullet points!\n"
        "   - DO NOT copy the DATA: format from catalog!\n"
        f"   - TRANSLATE labels (Name, Price, Link) to {detected_lang}.\n"
        "   - Put ###NEXT### BETWEEN each product (not at the end)\n\n"
        f"   CORRECT FORMAT for {detected_lang}:\n"
        f"   {'Товар' if user_language == 'ru' else 'Item'}: <item name>\n"
        f"   {'Цена' if user_language == 'ru' else 'Price'}: <price>\n"
        f"   {'Ссылка' if user_language == 'ru' else 'Link'}: <url>\n"
        "   ###NEXT###\n"
        f"   {'Товар' if user_language == 'ru' else 'Item'}: <another item>\n"
        f"   {'Цена' if user_language == 'ru' else 'Price'}: <price>\n"
        f"   {'Ссылка' if user_language == 'ru' else 'Link'}: <url>\n\n"

        "scenario_C: CONTACTS\n"
        "   - IF user asks for contacts/address/phone:\n"
        "   - 1. First check the 'KNOWLEDGE BASE' (files/answers) below.\n"
        "   - 2. If not found, use 'ORGANIZATION DATA' below.\n"
        f"   - TRANSLATE labels (Phone, Address, Hours) and Values to {detected_lang}.\n"
        "   - Required Format:\n"
        f"     📞 {'Телефон' if user_language == 'ru' else 'Phone'}: <Value>\n"
        f"     🏢 {'Адрес' if user_language == 'ru' else 'Address'}: <Value>\n"
        f"     🕘 {'Часы работы' if user_language == 'ru' else 'Hours'}: <Value> - <Value>\n"
        f"     Socials: {social_links} (if available)\n\n"

        "scenario_D: GENERAL QUESTIONS\n"
        "   - IF user asks general questions (Привет, Hello, etc.):\n"
        "   - Answer naturally and helpfully.\n"
        "   - Briefly describe what you can help with (products, promotions, contacts).\n"
        "   - DO NOT use ###NEXT### tag.\n"
        "   - DO NOT list products unless asked.\n\n"

        "🏁 ENDING RULE:\n"
        "   - ONLY when listing products, finish with organization link.\n"
        f"   - TRANSLATE the phrase 'More items at organization page' to {detected_lang}.\n"
        f"   - Format: ###NEXT###\n<Translated 'More items...'>: {organization_page_url}\n\n"

        "=== DATA SECTIONS ===\n\n"
    )

    # Add marketing/promotions
    if marketing_str:
        prompt += f"💰 ACTIVE PROMOTIONS:\n{marketing_str}\n\n"

    # Add organization data
    prompt += (
        f"🏢 ORGANIZATION DATA (Backup for contacts):\n"
        f"Phone: {phones_str}\n"
        f"Address: {address_str}\n"
        f"Open: {opens_at}\n"
        f"Close: {closes_at}\n\n"
    )

    # Add current item info if user is viewing a specific product
    if item_info:
        prompt += (
            f"📦 USER IS LOOKING AT THIS ITEM:\n"
            f"ID: {item_info.get('id')}\n"
            f"Name: {item_info.get('name')}\n"
            f"Price: {item_info.get('price')}\n"
            f"Description: {item_info.get('description')}\n\n"
        )

    # Add Q&A training data (KNOWLEDGE BASE)
    print(f"[BUILD_PROMPT] qa_pairs count: {len(qa_pairs) if qa_pairs else 0}")
    if qa_pairs:
        prompt += "📚 KNOWLEDGE BASE (Primary source for specific questions):\n"
        prompt += "IMPORTANT: When user asks for a link/file mentioned in answers below, provide the File URL!\n\n"
        for qa in qa_pairs:
            question = qa.get('question') or ''
            answer = qa.get('answer') or ''
            print(f"[BUILD_PROMPT] Adding Q&A: Q='{question[:50]}...' A='{answer[:50]}...'")
            if question and answer:
                prompt += f"Q: {question}\nA: {answer}\n"

            # Add file contents and URLs - use cached content if available
            files = qa.get('files') or []
            for file_url in files:
                if file_url:
                    # Always add the file URL so AI can share it
                    prompt += f"📎 File URL (share this when asked): {file_url}\n"

                    # Use cached content if available, otherwise download fresh
                    if cached_file_contents and file_url in cached_file_contents:
                        file_content = cached_file_contents[file_url]
                        print(f"[BUILD_PROMPT] Using cached file content: {file_url[:50]}...")
                    else:
                        print(f"[BUILD_PROMPT] Loading file (no cache): {file_url}")
                        file_content = read_file_from_url(file_url)

                    if file_content:
                        prompt += f"File content preview: {file_content[:1500]}\n"
                    else:
                        print("[BUILD_PROMPT] WARNING: Could not read file content, but URL is added")
            prompt += "\n"
    else:
        print("[BUILD_PROMPT] WARNING: No Q&A pairs provided!")

    # Add catalog (full catalog, same as website chat)
    if catalog_content:
        prompt += f"🛒 PRODUCT CATALOG:\n{catalog_content}\n"
        prompt += (
            "CATALOG RULES:\n"
            "- Search catalog for items matching user's request\n"
            "- Format each product using scenario_B format above\n"
            "- If nothing matches, say so and suggest alternatives\n\n"
        )

    # Add few-shot examples for better response quality (language-aware)
    org_name = assistant_info.get('organization', 'магазине')

    if user_language == "ru":
        prompt += (
            "📝 ПРИМЕРЫ ОТВЕТОВ:\n\n"
            "Пример 1 (Приветствие):\n"
            "User: Привет!\n"
            f"Assistant: Здравствуйте! Я помощник {org_name}. Могу помочь с информацией о товарах, акциях и контактах. Чем могу быть полезен?\n\n"
            "Пример 2 (Что умеешь):\n"
            "User: Что ты умеешь?\n"
            f"Assistant: Я могу помочь вам с информацией о товарах в {org_name}, рассказать об акциях и скидках, предоставить контактные данные и адрес. Задавайте вопросы!\n\n"
            "Пример 3 (Контакты):\n"
            "User: Как с вами связаться?\n"
            "Assistant: 📞 Телефон: +7 XXX XXX-XX-XX\n🏢 Адрес: ул. Примерная, 1\n🕘 Часы работы: 10:00 - 20:00\n\n"
        )
    else:
        prompt += (
            "📝 RESPONSE EXAMPLES:\n\n"
            "Example 1 (Greeting):\n"
            "User: Hello!\n"
            f"Assistant: Hello! I'm an assistant at {org_name}. I can help with product info, promotions, and contacts. How can I help you?\n\n"
            "Example 2 (Capabilities):\n"
            "User: What can you do?\n"
            f"Assistant: I can help you with product information at {org_name}, tell you about promotions and discounts, provide contact details and address. Feel free to ask!\n\n"
            "Example 3 (Contacts):\n"
            "User: How can I contact you?\n"
            "Assistant: 📞 Phone: +7 XXX XXX-XX-XX\n🏢 Address: Example St. 1\n🕘 Working hours: 10:00 - 20:00\n\n"
        )

    # Add language reminder at the end (same as Web Chat)
    prompt += (
        f"\n⚠️ REMINDER: The user speaks {detected_lang}. "
        f"Output ONLY in {detected_lang}. Translate all data if necessary.\n"
    )

    print(f"[BUILD_PROMPT] Final prompt length: {len(prompt)} chars")
    return prompt


# ============== OpenAI API ==============

def call_openai(
    question: str,
    system_prompt: str,
    chat_history: Optional[List[Dict[str, str]]] = None,
    model: str = "gpt-4o-mini",  # 128k context, cheaper than gpt-3.5-turbo
    max_tokens: int = 1500,
    temperature: float = 0.5,
) -> str:
    """
    Call OpenAI API via ai_assistant proxy service.

    The proxy is needed because the backend server may be in a region
    where OpenAI is blocked, but ai_assistant server is in allowed region.

    Args:
        question: User's question
        system_prompt: System prompt with training data
        chat_history: Previous messages for context
        model: OpenAI model name
        max_tokens: Maximum response tokens
        temperature: Response creativity (0-1)

    Returns:
        AI response text
    """
    # Get AI Assistant service URL for proxy
    ai_assistant_url = getattr(settings, "AI_ASSISTANT_URL", "http://161.35.153.151:8080")
    proxy_url = f"{ai_assistant_url}/bot/openai-proxy/"

    try:
        payload = {
            "system_prompt": system_prompt,
            "question": question,
            "chat_history": chat_history or [],
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        print(f"[AI_UTILS] Calling OpenAI proxy at {proxy_url}")
        session = get_http_session_with_retry()
        response = session.post(
            proxy_url,
            json=payload,
            timeout=(5, 30)  # (connect_timeout, read_timeout) - fast connection, reasonable read
        )

        result = response.json()

        if "answer" in result:
            answer = result["answer"]
            print(f"[AI_UTILS] OpenAI proxy response received: {len(answer)} chars")
            return answer
        elif "error" in result:
            print(f"[AI_UTILS] OpenAI proxy error: {result['error']}")
            return ""
        else:
            print(f"[AI_UTILS] Unexpected proxy response format: {result}")
            return ""

    except Exception as e:
        print(f"[AI_UTILS] Error calling OpenAI proxy: {e}")
        return ""


def get_openai_config():
    """Get OpenAI configuration from settings or cache."""
    from django.core.cache import cache

    api_key = cache.get('openai_api_key')
    model_name = cache.get('openai_model_name')

    if not api_key:
        api_key = getattr(settings, 'OPENAI_API_KEY', '')

    if not model_name:
        model_name = getattr(settings, 'OPENAI_MODEL_NAME', 'gpt-3.5-turbo')

    return api_key, model_name
