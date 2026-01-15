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

        text = "FULL ORGANIZATION CATALOG:\n"

        for item in items:
            name = item.get('name', 'Unknown Item')
            category = item.get('category', 'General')
            price = f"{item.get('price')} {item.get('currency', '')}" if item.get('price') else "Price not set"
            url = item.get('url', 'No link')

            description = (item.get('description') or "").strip().replace("\n", " ")
            if len(description) > 300:
                description = description[:297] + "..."

            text += f"- [{category}] {name} (Price: {price}). Link: {url}\n"
            if description:
                text += f"  Info: {description}\n"

        return text

    except Exception as e:
        print(f"Error parsing catalog JSON: {e}")
        return ""


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

    # Direct match
    if keyword in text:
        return True

    # Try stems of keyword in text
    for stem in get_word_stems(keyword):
        if len(stem) >= 3 and stem in text:
            return True

    # Try if any word in text starts with keyword stem
    text_words = text.split()
    keyword_stems = get_word_stems(keyword)
    for text_word in text_words:
        for stem in keyword_stems:
            if len(stem) >= 3 and text_word.startswith(stem):
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
        matched_items = []
        for item in items:
            name = (item.get('name') or '').lower()
            category = (item.get('category') or '').lower()
            description = (item.get('description') or '').lower()
            searchable_text = f"{name} {category} {description}"

            # Check if any keyword matches using flexible matching
            for keyword in keywords:
                if keyword_matches_text(keyword, searchable_text):
                    matched_items.append(item)
                    break

        print(f"[CATALOG_FILTER] Found {len(matched_items)} items matching keywords {keywords}")

        if not matched_items:
            # No matches - return full catalog with note
            print("[CATALOG_FILTER] No matches found, returning full catalog")
            return format_catalog_json(json_content.encode('utf-8') if isinstance(json_content, str) else json_content)

        # Format matched items with explicit instruction
        text = f"✅ FOUND {len(matched_items)} PRODUCTS matching user query. YOU MUST LIST THESE ITEMS:\n"

        for item in matched_items:
            name = item.get('name', 'Unknown Item')
            category = item.get('category', 'General')
            price = f"{item.get('price')} {item.get('currency', '')}" if item.get('price') else "Price not set"
            url = item.get('url', 'No link')

            description = (item.get('description') or "").strip().replace("\n", " ")
            if len(description) > 300:
                description = description[:297] + "..."

            text += f"- [{category}] {name} (Price: {price}). Link: {url}\n"
            if description:
                text += f"  Info: {description}\n"

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

        file_url_lower = file_url.lower()

        if file_url_lower.endswith(".pdf"):
            return extract_text_from_pdf(file_content)
        elif file_url_lower.endswith(".docx"):
            return extract_text_from_docx(file_content)
        elif file_url_lower.endswith(".json"):
            return format_catalog_json(file_content)
        elif file_url_lower.endswith((".txt", ".csv", ".log", ".md")):
            try:
                return file_content.decode("utf-8")[:5000]
            except UnicodeDecodeError:
                print(f"Failed to decode file as UTF-8: {file_url}")
                return ""
        else:
            print(f"Unsupported file type for text extraction: {file_url}")
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

    The product format is designed to be compatible with telegram.py's
    parse_products_from_response() function which expects:
    - "Товар:" or "Product:" at the start
    - "Ссылка:" or "Link:" with URL at the end
    """
    # Extract contact info
    phones_str = ", ".join(organization_info.get('phones', []))
    address_str = organization_info.get('address', 'Unknown')
    opens_at = organization_info.get('opens_at', 'Unknown')
    closes_at = organization_info.get('closes_at', 'Unknown')
    social_links = organization_info.get('social_links', '')

    # Language-specific labels
    if user_language == "en":
        product_label = "Product"
        category_label = "Category"
        price_label = "Price"
        link_label = "Link"
        more_products_text = f"More products on the organization page: {organization_page_url}"
        phone_label = "Phone"
        address_label = "Address"
        hours_label = "Working hours"
    else:
        product_label = "Товар"
        category_label = "Категория"
        price_label = "Цена"
        link_label = "Ссылка"
        more_products_text = f"Больше товаров на странице организации: {organization_page_url}"
        phone_label = "Телефон"
        address_label = "Адрес"
        hours_label = "Часы работы"

    prompt = (
        f"You are {assistant_info.get('name', 'Assistant')}, "
        f"{assistant_info.get('position', 'consultant')} at {assistant_info.get('organization', 'organization')}. "
        f"Gender: {assistant_info.get('gender', 'not specified')}.\n\n"

        "FORMATTING RULES:\n"
        "- NO markdown (*, **, _, ~, `, [text](url))\n"
        "- Links as plain text only\n\n"

        "PRODUCT FORMAT (use exactly):\n"
        f"{product_label}: <Name>\n"
        f"{category_label}: <Category>\n"
        f"{price_label}: <Price>\n"
        f"{link_label}: <URL>\n"
        "###NEXT###\n\n"

        "PRODUCT RULES:\n"
        f"- Each product needs: {product_label}, {category_label}, {price_label}, {link_label}\n"
        "- Use ###NEXT### between products\n"
        "- No numbering (1., 2.)\n"
        f"- End with: ###NEXT###\n  {more_products_text}\n\n"

        f"CONTACTS (when asked):\n"
        f"{phone_label}: {phones_str}\n"
        f"{address_label}: {address_str}\n"
        f"{hours_label}: {opens_at} - {closes_at}\n"
    )

    if social_links:
        prompt += f"   Social links: {social_links}\n"

    prompt += "\n"

    # Add marketing/promotions
    if marketing_info:
        marketing_str = "\n".join([f"- {m}" for m in marketing_info])
        prompt += (
            f"PROMOTIONS & DISCOUNTS:\n"
            f"{marketing_str}\n"
            f"(Mention these if the user asks about price, discounts or bonuses)\n\n"
        )

    # Add current item info if user is viewing a specific product
    if item_info:
        prompt += (
            f"USER IS CURRENTLY VIEWING THIS ITEM:\n"
            f"ID: {item_info.get('id')}\n"
            f"Name: {item_info.get('name')}\n"
            f"Price: {item_info.get('price')}\n"
            f"Description: {item_info.get('description')}\n\n"
        )

    # Add Q&A training data
    if qa_pairs:
        prompt += "KNOWLEDGE BASE (Q&A):\n"
        for qa in qa_pairs:
            question = qa.get('question', '')
            answer = qa.get('answer', '')
            if question and answer:
                prompt += f"Q: {question}\nA: {answer}\n"

            # Add file contents and URLs
            for file_url in qa.get('files', []):
                if file_url:
                    file_content = read_file_from_url(file_url)
                    if file_content:
                        prompt += f"File content: {file_content[:2000]}\n"
                        prompt += f"File link (if needed): {file_url}\n"
        prompt += "\n"

    # Add catalog
    if catalog_content:
        prompt += (
            f"=== CATALOG ===\n{catalog_content}\n"
            "CATALOG RULES:\n"
            "- If catalog header says 'FOUND X PRODUCTS' - these items MATCH user's query, LIST THEM ALL\n"
            "- DO NOT say 'products not found' if catalog contains items\n"
            "- Format each product using PRODUCT FORMAT above\n\n"
        )

    prompt += (
        "BEHAVIOR: Be concise, polite. If unsure, suggest contacting organization.\n"
    )

    return prompt


# ============== OpenAI API ==============

def call_openai(
    question: str,
    system_prompt: str,
    chat_history: Optional[List[Dict[str, str]]] = None,
    model: str = "gpt-3.5-turbo",
    max_tokens: int = 1500,
    temperature: float = 0.7,
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
