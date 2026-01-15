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


def should_load_catalog(question: str) -> bool:
    """
    Determine if the question is about products/catalog.
    Returns True only if user is clearly asking about products.

    This prevents loading 20KB catalog for simple questions like "Привет!" or "Что ты умеешь?"
    """
    question_lower = question.lower().strip()

    # Product-related trigger words (user wants to see products)
    product_triggers = {
        # Russian - asking for products
        'товар', 'товары', 'продукт', 'продукция', 'каталог', 'ассортимент',
        'купить', 'покупка', 'заказать', 'заказ', 'приобрести',
        'покажи', 'покажите', 'показать', 'посмотреть',
        'есть ли', 'имеется', 'в наличии', 'наличие',
        'цена', 'цены', 'стоимость', 'сколько стоит', 'прайс',
        'ссылка', 'ссылку', 'скинь',  # Links to files/services
        # Russian - product categories (common)
        'кроссовки', 'кеды', 'обувь', 'ботинки', 'сапоги', 'туфли',
        'сумка', 'сумки', 'рюкзак', 'рюкзаки', 'клатч',
        'одежда', 'платье', 'юбка', 'блузка', 'футболка', 'джинсы',
        'куртка', 'пальто', 'шуба', 'плащ',
        'купальник', 'купальники', 'бикини',
        'аксессуары', 'украшения', 'часы', 'очки',
        # English
        'product', 'products', 'catalog', 'catalogue', 'item', 'items',
        'buy', 'purchase', 'order', 'show me', 'looking for',
        'price', 'prices', 'cost', 'how much',
        'shoes', 'sneakers', 'bags', 'clothes', 'dress',
    }

    # Check if any trigger is in the question
    for trigger in product_triggers:
        if trigger in question_lower:
            print(f"[CATALOG_FILTER] Product trigger found: '{trigger}' in '{question}'")
            return True

    # Check for product-asking patterns
    product_patterns = [
        'что у вас есть',
        'что есть',
        'что продаёте',
        'что продаете',
        'чем торгуете',
        'what do you have',
        'what do you sell',
    ]
    for pattern in product_patterns:
        if pattern in question_lower:
            print(f"[CATALOG_FILTER] Product pattern found: '{pattern}'")
            return True

    print(f"[CATALOG_FILTER] No product triggers in '{question}' - skipping catalog")
    return False


def extract_search_keywords(question: str) -> List[str]:
    """
    Extract potential product keywords from user question.
    Returns list of keywords to search in catalog.
    """
    # Common stop words to ignore
    stop_words = {
        'покажи', 'покажите', 'есть', 'ли', 'у', 'вас', 'меня', 'мне',
        'хочу', 'нужен', 'нужна', 'нужно', 'нужны', 'можно', 'какие',
        'что', 'где', 'как', 'сколько', 'стоит', 'цена', 'купить',
        'посмотреть', 'показать', 'найти', 'ищу', 'интересует',
        'подскажите', 'расскажите', 'а', 'и', 'в', 'на', 'с', 'по',
        'для', 'от', 'до', 'или', 'но', 'же', 'бы', 'то', 'не',
        'дай', 'дайте', 'список', 'товаров', 'товары', 'все', 'всё',
        'продукты', 'продукция', 'ассортимент', 'каталог', 'весь',
        'show', 'me', 'do', 'you', 'have', 'any', 'want', 'need',
        'looking', 'for', 'find', 'search', 'the', 'a', 'an', 'is', 'are',
        'list', 'all', 'products', 'items', 'catalog', 'give', 'get',
    }

    # Clean and split question
    question_lower = question.lower()
    # Remove punctuation
    for char in '?!.,;:()[]{}"\'-':
        question_lower = question_lower.replace(char, ' ')

    words = question_lower.split()

    # Filter keywords (length > 2, not in stop words)
    keywords = [w for w in words if len(w) > 2 and w not in stop_words]

    print(f"[CATALOG_FILTER] Extracted keywords from '{question}': {keywords}")
    return keywords


def get_word_stems(word: str) -> List[str]:
    """
    Get possible stems of a Russian/English word by removing common suffixes.
    Returns list of possible stems including the original word.
    """
    stems = [word]
    if len(word) < 4:
        return stems

    # Russian plural/case endings (most common)
    russian_suffixes = ['ики', 'ами', 'ами', 'ями', 'ов', 'ев', 'ей', 'ах', 'ях', 'ие', 'ые', 'ий', 'ый', 'ая', 'яя', 'ое', 'ее', 'и', 'ы', 'а', 'я', 'у', 'ю', 'е', 'о']

    for suffix in russian_suffixes:
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            stems.append(word[:-len(suffix)])

    # Also add truncated versions (last 1-2 chars removed)
    if len(word) > 4:
        stems.append(word[:-1])
        stems.append(word[:-2])

    return list(set(stems))  # Remove duplicates


def keyword_matches_text(keyword: str, text: str) -> bool:
    """
    Check if keyword matches text using flexible matching.
    Handles Russian morphology (plural/singular, cases).
    """
    if not keyword or not text:
        return False

    # Minimum keyword length to avoid false positives
    if len(keyword) < 3:
        return False

    # Direct match - most reliable
    if keyword in text:
        return True

    # For short keywords (3-4 chars), require exact word match only
    if len(keyword) <= 4:
        text_words = text.split()
        return keyword in text_words

    # Try stems of keyword in text (only for longer words)
    min_stem_len = 4  # Increased from 3 to reduce false positives
    for stem in get_word_stems(keyword):
        if len(stem) >= min_stem_len and stem in text:
            return True

    # Try if any word in text starts with keyword stem
    text_words = text.split()
    keyword_stems = get_word_stems(keyword)
    for text_word in text_words:
        for stem in keyword_stems:
            # Only match if stem is substantial part of the keyword
            if len(stem) >= min_stem_len and len(stem) >= len(keyword) - 2:
                if text_word.startswith(stem):
                    return True

    return False


def filter_catalog_by_keywords(json_content, keywords: List[str]) -> str:
    """
    Filter catalog items by keywords and format for AI.
    Returns filtered catalog text or full catalog if no matches.
    """
    try:
        if isinstance(json_content, bytes):
            json_content = json_content.decode('utf-8')

        items = json.loads(json_content)
        if not items:
            return "Catalog is empty."

        if not keywords:
            # No keywords - return full catalog
            print("[CATALOG_FILTER] No keywords extracted, returning full catalog")
            return format_catalog_json(json_content.encode('utf-8') if isinstance(json_content, str) else json_content)

        print(f"[CATALOG_FILTER] Searching for keywords: {keywords}")

        # Filter items matching any keyword
        # Priority: name > category > description (description has more noise)
        matched_items = []
        for item in items:
            name = (item.get('name') or '').lower()
            category = (item.get('category') or '').lower()

            # Primary search: name and category only (most reliable)
            primary_text = f"{name} {category}"

            for keyword in keywords:
                if keyword_matches_text(keyword, primary_text):
                    matched_items.append(item)
                    break

        print(f"[CATALOG_FILTER] Found {len(matched_items)} items matching keywords {keywords}")

        if not matched_items:
            # No matches - return full catalog with note
            print("[CATALOG_FILTER] No matches found, returning full catalog")
            return format_catalog_json(json_content.encode('utf-8') if isinstance(json_content, str) else json_content)

        # Format matched items - use structured data format (NOT the response format!)
        # AI should reformat these into scenario_B format with ###NEXT###
        text = f"✅ FOUND {len(matched_items)} PRODUCTS:\n"
        text += "(IMPORTANT: Reformat each item using scenario_B format with ###NEXT### separator!)\n\n"

        for item in matched_items:
            name = item.get('name', 'Unknown Item')
            category = item.get('category', 'General')
            price = f"{item.get('price')} {item.get('currency', '')}" if item.get('price') else "Price not set"
            url = item.get('url', 'No link')

            description = (item.get('description') or "").strip().replace("\n", " ")
            if len(description) > 150:
                description = description[:147] + "..."

            # Use DATA: prefix to make it clear this is raw data, not response format
            text += f"DATA: name={name} | category={category} | price={price} | url={url}\n"

        return text

    except Exception as e:
        print(f"[CATALOG_FILTER] Error filtering catalog: {e}")
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
) -> str:
    """
    Build a comprehensive system prompt for the AI assistant.
    Structure copied from ai_assistant/bot/consumers.py for consistency.

    The product format is designed to be compatible with telegram.py's
    parse_products_from_response() function which expects:
    - "Товар:" or "Product:" at the start
    - "Ссылка:" or "Link:" with URL at the end
    """
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

    # Build prompt - SAME STRUCTURE AS consumers.py
    prompt = (
        f"SYSTEM PRIORITY: DETECT USER LANGUAGE (e.g., Russian, English). "
        f"You MUST answer STRICTLY in the same language as the user's question.\n\n"

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
        "   - DO NOT use the ###NEXT### tag in this scenario.\n\n"

        "scenario_B: PRODUCTS (Catalogue)\n"
        "   ⚠️ CRITICAL: You MUST use this EXACT format for EACH product:\n"
        "   - DO NOT use dashes (-) or bullet points!\n"
        "   - DO NOT copy the DATA: format from catalog!\n"
        "   - TRANSLATE labels to user's language (Russian: Товар/Цена/Ссылка)\n"
        "   - Put ###NEXT### BETWEEN each product (not at the end)\n\n"
        "   CORRECT FORMAT (Russian example):\n"
        "   Товар: Название товара\n"
        "   Цена: 1000 RUB\n"
        "   Ссылка: https://...\n"
        "   ###NEXT###\n"
        "   Товар: Другой товар\n"
        "   Цена: 2000 RUB\n"
        "   Ссылка: https://...\n\n"

        "scenario_C: CONTACTS\n"
        "   - IF user asks for contacts/address/phone:\n"
        "   - 1. First check the 'KNOWLEDGE BASE' (files/answers) below.\n"
        "   - 2. If not found, use 'ORGANIZATION DATA' below.\n"
        "   - TRANSLATE labels (Phone, Address, Hours) to user's language.\n"
        "   - Required Format:\n"
        "     📞 <Translated 'Phone'>: <Value>\n"
        "     🏢 <Translated 'Address'>: <Value>\n"
        "     🕘 <Translated 'Hours'>: <Value> - <Value>\n"
        f"     Socials: {social_links} (if available)\n\n"

        "scenario_D: GENERAL QUESTIONS\n"
        "   - IF user asks general questions (Привет, Что ты умеешь?, etc.):\n"
        "   - Answer naturally and helpfully.\n"
        "   - Briefly describe what you can help with (products, promotions, contacts).\n"
        "   - DO NOT use ###NEXT### tag.\n"
        "   - DO NOT list products unless asked.\n\n"

        "🏁 ENDING RULE:\n"
        "   - ONLY when listing products, finish with organization link.\n"
        "   - Translate the phrase 'More items at organization page' to user's language.\n"
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
            question = qa.get('question', '')
            answer = qa.get('answer', '')
            print(f"[BUILD_PROMPT] Adding Q&A: Q='{question[:50]}...' A='{answer[:50]}...'")
            if question and answer:
                prompt += f"Q: {question}\nA: {answer}\n"

            # Add file contents and URLs - ALWAYS add URL even if content fails
            files = qa.get('files', [])
            for file_url in files:
                if file_url:
                    print(f"[BUILD_PROMPT] Loading file: {file_url}")
                    # Always add the file URL so AI can share it
                    prompt += f"📎 File URL (share this when asked): {file_url}\n"

                    # Try to extract content for context
                    file_content = read_file_from_url(file_url)
                    if file_content:
                        prompt += f"File content preview: {file_content[:1500]}\n"
                    else:
                        print("[BUILD_PROMPT] WARNING: Could not read file content, but URL is added")
            prompt += "\n"
    else:
        print("[BUILD_PROMPT] WARNING: No Q&A pairs provided!")

    # Add catalog with strict rules
    if catalog_content:
        # Check if catalog is filtered (has FOUND X PRODUCTS header)
        is_filtered = "✅ FOUND" in catalog_content

        prompt += f"🛒 PRODUCT CATALOG:\n{catalog_content}\n"

        if is_filtered:
            # Filtered catalog - products already match user's query
            prompt += (
                "⚠️ CATALOG STATUS: PRE-FILTERED - items above MATCH user's query!\n\n"
                "CATALOG RESPONSE RULES (STRICT):\n"
                "1. NEVER say 'not found' / 'нет в каталоге' - products ARE found above\n"
                "2. If user said 'покажи/список/дай/show/list' → LIST ALL products above\n"
                "3. If user said 'есть ли/есть/have' → Confirm: 'Да, есть!' + show 1-2 examples\n"
                "4. Format each product using scenario_B format above\n\n"
            )
        else:
            # Full catalog - user asked general question
            prompt += (
                "CATALOG STATUS: FULL - all available products shown.\n"
                "Use this to recommend items if asked.\n\n"
            )

    # Add few-shot examples for better response quality
    org_name = assistant_info.get('organization', 'магазине')
    prompt += (
        "📝 RESPONSE EXAMPLES:\n\n"

        "Example 1 (General greeting):\n"
        "User: Привет!\n"
        f"Assistant: Здравствуйте! Я помощник {org_name}. Могу помочь с информацией о товарах, акциях и контактах. Чем могу быть полезен?\n\n"

        "Example 2 (What can you do):\n"
        "User: Что ты умеешь?\n"
        f"Assistant: Я могу помочь вам с информацией о товарах в {org_name}, рассказать об акциях и скидках, предоставить контактные данные и адрес. Задавайте вопросы!\n\n"

        "Example 3 (Contacts):\n"
        "User: Как с вами связаться?\n"
        "Assistant: 📞 Телефон: +7 XXX XXX-XX-XX\n🏢 Адрес: ул. Примерная, 1\n🕘 Часы работы: 10:00 - 20:00\n\n"
    )

    print(f"[BUILD_PROMPT] Final prompt length: {len(prompt)} chars")
    return prompt


# ============== OpenAI API ==============

def call_openai(
    question: str,
    system_prompt: str,
    chat_history: Optional[List[Dict[str, str]]] = None,
    model: str = "gpt-3.5-turbo",
    max_tokens: int = 1500,
    temperature: float = 0.5,  # Same as consumers.py for consistency
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
