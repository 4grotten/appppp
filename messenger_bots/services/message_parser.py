"""
Shared message parsing utilities for Telegram and WhatsApp bots.

This module provides unified parsing for AI responses containing products,
ensuring consistent behavior across all messenger platforms.
"""
import re
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)

# AI separator used between products
AI_SEPARATOR = "###NEXT###"

# Product validation pattern - matches both Russian and English formats
# Expected format:
# Russian: Товар: ... Ссылка: URL
# English: Product: ... Link: URL
PRODUCT_PATTERN = re.compile(
    r'((?:Товар|Product|Item):.*?(?:Ссылка|Link):\s*https?://[^\s]+)',
    re.DOTALL | re.IGNORECASE
)

# Footer pattern - matches closing text
FOOTER_PATTERN = re.compile(
    r'((?:Больше товаров|More items|More products).+)$',
    re.DOTALL | re.IGNORECASE
)


def parse_products_from_response(ai_response: str) -> Tuple[List[str], str]:
    """
    Parse AI response and split into separate product blocks.

    Uses hybrid approach for maximum reliability:
    1. If ###NEXT### separators present - split by them first (faster)
    2. Validate each block with regex (ensures correct format)
    3. Fallback to pure regex if no separators (handles edge cases)

    Supports both Russian and English formats:
    - Russian: Товар: ... Ссылка: URL
    - English: Product: ... Link: URL

    Args:
        ai_response: Raw AI response text

    Returns:
        Tuple of (products list, footer text)
        - products: list of validated product blocks
        - footer: closing text ("Больше товаров..."/"More items...")
    """
    products = []

    # Step 1: Extract footer first (before processing)
    footer = ""
    footer_match = FOOTER_PATTERN.search(ai_response)
    if footer_match:
        footer = footer_match.group(1).strip()
        # Remove ###NEXT### from footer if present
        footer = footer.replace(AI_SEPARATOR, "").strip()

    # Step 2: Clean response - remove footer from parsing
    clean_response = ai_response
    if footer:
        clean_response = ai_response[:ai_response.rfind(footer)].strip()

    # Step 3: Hybrid parsing approach
    if AI_SEPARATOR in clean_response:
        # Fast path: split by ###NEXT### and validate each block
        logger.debug("[PARSER] Using ###NEXT### separator parsing")
        blocks = clean_response.split(AI_SEPARATOR)

        for block in blocks:
            block = block.strip()
            if not block:
                continue

            # Validate block has correct product format
            match = PRODUCT_PATTERN.search(block)
            if match:
                products.append(match.group(1).strip())
    else:
        # Fallback: pure regex parsing (handles any format)
        logger.debug("[PARSER] Using regex-only parsing")
        matches = PRODUCT_PATTERN.findall(clean_response)
        products = [m.strip() for m in matches if m.strip()]

    # Step 4: Deduplicate while preserving order
    seen = set()
    unique_products = []
    for p in products:
        if p not in seen:
            seen.add(p)
            unique_products.append(p)

    logger.debug(f"[PARSER] Parsed {len(unique_products)} products, footer: {bool(footer)}")
    return unique_products, footer


def clean_response(ai_response: str) -> str:
    """
    Clean AI response by removing ###NEXT### separators.

    Use this for responses that don't need product parsing
    (e.g., greetings, contact info).

    Args:
        ai_response: Raw AI response text

    Returns:
        Cleaned text with separators replaced by newlines
    """
    return ai_response.replace(AI_SEPARATOR, "\n\n").strip()


def split_by_separator(ai_response: str) -> List[str]:
    """
    Split AI response by ###NEXT### separator.

    Returns list of non-empty parts.

    Args:
        ai_response: Raw AI response text

    Returns:
        List of message parts
    """
    if AI_SEPARATOR not in ai_response:
        return [ai_response.strip()] if ai_response.strip() else []

    parts = []
    for part in ai_response.split(AI_SEPARATOR):
        part = part.strip()
        if part:
            parts.append(part)

    return parts


def has_products(ai_response: str) -> bool:
    """
    Check if AI response contains product listings.

    Args:
        ai_response: Raw AI response text

    Returns:
        True if response contains products
    """
    return bool(PRODUCT_PATTERN.search(ai_response))
