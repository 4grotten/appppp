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

        logger.error("No PDF library available (pypdf, PyPDF2, or pdfplumber)")
        return ""

    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
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

        logger.error("No DOCX library available (python-docx)")
        return ""

    except Exception as e:
        logger.error(f"Error extracting text from DOCX: {e}")
        return ""


def format_catalog_json(json_content: bytes) -> str:
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
        logger.error(f"Error parsing catalog JSON: {e}")
        return ""


def read_file_from_url(file_url: str) -> str:
    """
    Read and extract text content from a file URL.
    Supports: PDF, DOCX, JSON, TXT, CSV, MD

    Uses HTTP session with automatic retry on server errors.
    """
    try:
        session = get_http_session_with_retry()
        response = session.get(file_url, timeout=30)
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
                logger.error(f"Failed to decode file as UTF-8: {file_url}")
                return ""
        else:
            logger.warning(f"Unsupported file type for text extraction: {file_url}")
            return ""

    except requests.exceptions.RequestException as e:
        logger.error(f"Error reading file from URL: {e}")
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
        f"You are a helpful assistant named {assistant_info.get('name', 'Assistant')} "
        f"working for {assistant_info.get('organization', 'the organization')}.\n"
        f"Your position: {assistant_info.get('position', 'consultant')}. "
        f"Gender: {assistant_info.get('gender', 'not specified')}.\n\n"

        "STRICT FORMATTING RULES (CRITICAL):\n"
        "1. NO MARKDOWN ALLOWED. Do not use *, **, _, ~, `, [text](url).\n"
        "2. Send LINKS as plain text only (e.g. https://site.com).\n\n"

        "PRODUCT RECOMMENDATIONS FORMAT:\n"
        "When recommending multiple products, use EXACTLY this format:\n"
        f"   {product_label}: <Name>\n"
        f"   {category_label}: <Category>\n"
        f"   {price_label}: <Price>\n"
        f"   {link_label}: <URL>\n"
        "   ###NEXT###\n"
        f"   {product_label}: <Next product name>\n"
        "   ... (repeat for each product)\n\n"

        "IMPORTANT RULES:\n"
        f"- Each product MUST have all 4 lines ({product_label}, {category_label}, {price_label}, {link_label})\n"
        f"- The {link_label} line MUST contain a valid https:// URL\n"
        "- Use ###NEXT### separator between products\n"
        "- Do NOT number products (1., 2., etc.)\n\n"

        f"ALWAYS finish product recommendations with:\n"
        f"   ###NEXT###\n"
        f"   {more_products_text}\n\n"

        "ORGANIZATION CONTACTS FORMAT:\n"
        "If the user asks for contacts/address/phone, use EXACTLY this format:\n"
        f"   {phone_label}: {phones_str}\n"
        f"   {address_label}: {address_str}\n"
        f"   {hours_label}: {opens_at} - {closes_at}\n"
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

    # Add catalog with detailed instructions
    if catalog_content:
        prompt += (
            f"=== COMPANY PRODUCT CATALOG ===\n{catalog_content}\n"
            "CATALOG USAGE INSTRUCTIONS:\n"
            "- Use this catalog to answer ANY questions about products, prices, and availability.\n"
            "- Help the client find products they might be interested in, not just specific items they ask about.\n"
            "- Proactively suggest alternatives if the requested item is not available or if similar products exist.\n"
            "- Always provide prices and links from this catalog when recommending products.\n"
            "- If a product is not in the catalog, clearly state that and suggest similar items if available.\n\n"
        )

    prompt += (
        "CONTEXT INSTRUCTIONS:\n"
        "- Remember the user's last selected filters (category, price) from the current conversation.\n"
        "- If the user asks about 'this' or 'it', refer to the last discussed item.\n"
        "- Keep answers concise and polite.\n"
        "- If you don't know the answer, suggest contacting the organization directly.\n"
    )

    return prompt


# ============== OpenAI API ==============

def call_openai(
    question: str,
    system_prompt: str,
    chat_history: Optional[List[Dict[str, str]]] = None,
    model: str = "gpt-3.5-turbo",
    max_tokens: int = 500,
    temperature: float = 0.7,
) -> str:
    """
    Call OpenAI API directly.

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
    api_key = getattr(settings, "OPENAI_API_KEY", None)
    if not api_key:
        logger.error("OPENAI_API_KEY not configured!")
        return ""

    try:
        # Build messages array
        messages = [{"role": "system", "content": system_prompt}]

        # Add chat history for context
        if chat_history:
            for msg in chat_history[-10:]:  # Last 10 messages
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
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        logger.debug(f"[AI_UTILS] Calling OpenAI API with model={model}")
        session = get_http_session_with_retry()
        response = session.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )

        result = response.json()

        if "choices" in result and len(result["choices"]) > 0:
            answer = result["choices"][0]["message"]["content"].strip()
            logger.info(f"[AI_UTILS] OpenAI response received: {len(answer)} chars")
            return answer
        else:
            logger.error(f"[AI_UTILS] Unexpected API response format: {result}")
            return ""

    except Exception as e:
        logger.error(f"[AI_UTILS] Error calling OpenAI: {e}")
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
