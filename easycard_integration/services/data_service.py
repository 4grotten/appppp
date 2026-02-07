"""Data service for EasyCard integration.

Provides cached access to EasyCard user financial data.
Used by OTP Bot AI to provide personalized responses.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from django.core.cache import cache
from django.db import DatabaseError
from django.utils import timezone

logger = logging.getLogger(__name__)

# Cache settings
EASYCARD_CACHE_PREFIX = "easycard_"
EASYCARD_CACHE_TTL = 300  # 5 minutes
EASYCARD_SETTINGS_CACHE_TTL = 600  # 10 minutes


@dataclass
class UserFinancialData:
    """Structured user financial data for AI context."""

    phone: str
    user_id: Optional[str]
    full_name: str
    total_balance: Decimal
    cards: List[Dict[str, Any]]
    recent_transactions: List[Dict[str, Any]]
    has_active_card: bool
    is_registered: bool

    def to_ai_context(self) -> str:
        """Format financial data as AI context string."""
        if not self.is_registered:
            return "Пользователь не найден в базе EasyCard."

        parts = [
            f"## Информация о пользователе {self.full_name}",
            f"- Общий баланс: {self.total_balance} AED",
            f"- Активная карта: {'Да' if self.has_active_card else 'Нет'}",
        ]

        # Add cards info
        if self.cards:
            parts.append("\n### Карты:")
            for card in self.cards:
                status_ru = {
                    "active": "Активна",
                    "inactive": "Неактивна",
                    "blocked": "Заблокирована",
                    "expired": "Истекла",
                }.get(card["status"], card["status"])
                type_ru = {"virtual": "Виртуальная", "metal": "Металлическая"}.get(
                    card["type"], card["type"]
                )
                parts.append(
                    f"- {card['name']} ({type_ru}): {card['balance']} AED ({status_ru})"
                )

        # Add recent transactions
        if self.recent_transactions:
            parts.append("\n### Последние транзакции:")
            for tx in self.recent_transactions[:5]:
                type_ru = {
                    "top_up": "Пополнение",
                    "withdrawal": "Снятие",
                    "transfer_in": "Входящий перевод",
                    "transfer_out": "Исходящий перевод",
                    "card_payment": "Оплата картой",
                    "refund": "Возврат",
                    "fee": "Комиссия",
                    "cashback": "Кэшбэк",
                    "card_activation": "Активация карты",
                }.get(tx["type"], tx["type"])
                date_str = tx["created_at"].strftime("%d.%m.%Y")
                amount = tx["amount"]
                desc = tx.get("description") or tx.get("merchant_name") or ""
                parts.append(f"- {date_str}: {type_ru} {amount} AED {desc}")
        else:
            parts.append("\n### Последние транзакции: нет")

        return "\n".join(parts)


class EasyCardDataService:
    """Service for accessing EasyCard user data.

    Provides cached read-only access to EasyCard PostgreSQL database.
    Used by OTP Bot AI for personalized financial responses.

    Usage:
        data = EasyCardDataService.get_user_financial_data("+971501234567")
        context = data.to_ai_context()
    """

    @classmethod
    def get_user_financial_data(
        cls,
        phone_number: str,
        include_transactions: bool = True,
        transaction_limit: int = 10,
    ) -> UserFinancialData:
        """Get user's financial data by phone number.

        Args:
            phone_number: User's phone number (any format)
            include_transactions: Whether to include recent transactions
            transaction_limit: Max number of transactions to fetch

        Returns:
            UserFinancialData object with all available information
        """
        normalized_phone = cls._normalize_phone(phone_number)
        cache_key = f"{EASYCARD_CACHE_PREFIX}user_{normalized_phone}"

        # Try cache first
        cached = cache.get(cache_key)
        if cached is not None:
            logger.debug(f"[EASYCARD] Cache hit for {cls._mask_phone(normalized_phone)}")
            return cached

        # Fetch from database
        try:
            data = cls._fetch_user_data(
                normalized_phone, include_transactions, transaction_limit
            )
            cache.set(cache_key, data, timeout=EASYCARD_CACHE_TTL)
            logger.info(
                f"[EASYCARD] Fetched data for {cls._mask_phone(normalized_phone)}: "
                f"registered={data.is_registered}"
            )
            return data

        except DatabaseError as e:
            logger.error(f"[EASYCARD] Database error: {e}")
            return cls._empty_user_data(normalized_phone)
        except Exception as e:
            logger.error(f"[EASYCARD] Error fetching data: {e}", exc_info=True)
            return cls._empty_user_data(normalized_phone)

    @classmethod
    def _fetch_user_data(
        cls, phone: str, include_transactions: bool, transaction_limit: int
    ) -> UserFinancialData:
        """Fetch user data from EasyCard database."""
        from ..models import EasyCardCard, EasyCardProfile, EasyCardTransaction

        # Find profile by phone
        profile = EasyCardProfile.objects.filter(phone=phone).first()

        if not profile:
            # Try without + prefix
            alt_phone = phone.lstrip("+")
            profile = EasyCardProfile.objects.filter(phone=alt_phone).first()

        if not profile:
            return cls._empty_user_data(phone)

        # Get user's cards
        cards = list(
            EasyCardCard.objects.filter(user_id=profile.user_id).values(
                "id",
                "name",
                "type",
                "status",
                "balance",
                "last_four_digits",
                "expiry_date",
            )
        )

        # Calculate total balance
        total_balance = sum(
            card["balance"] for card in cards if card["status"] == "active"
        )

        has_active_card = any(card["status"] == "active" for card in cards)

        # Get recent transactions
        transactions = []
        if include_transactions:
            transactions = list(
                EasyCardTransaction.objects.filter(user_id=profile.user_id)
                .order_by("-created_at")[:transaction_limit]
                .values(
                    "id",
                    "type",
                    "status",
                    "amount",
                    "currency",
                    "fee",
                    "merchant_name",
                    "description",
                    "created_at",
                )
            )

        return UserFinancialData(
            phone=phone,
            user_id=str(profile.user_id),
            full_name=profile.full_name,
            total_balance=Decimal(str(total_balance)),
            cards=cards,
            recent_transactions=transactions,
            has_active_card=has_active_card,
            is_registered=True,
        )

    @classmethod
    def get_exchange_rates(cls) -> Dict[str, Decimal]:
        """Get current exchange rates from EasyCard settings.

        Returns:
            Dict mapping currency pairs to rates.
            Example: {'usdt_aed_buy': 3.65, 'usdt_aed_sell': 3.69}
        """
        cache_key = f"{EASYCARD_CACHE_PREFIX}exchange_rates"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            from ..models import EasyCardAdminSettings

            rates = {}
            settings = EasyCardAdminSettings.objects.filter(category="exchange_rates")
            for setting in settings:
                rates[setting.key] = setting.value

            cache.set(cache_key, rates, timeout=EASYCARD_SETTINGS_CACHE_TTL)
            return rates

        except Exception as e:
            logger.error(f"[EASYCARD] Error fetching exchange rates: {e}")
            # Return default rates
            return {
                "usdt_aed_buy": Decimal("3.65"),
                "usdt_aed_sell": Decimal("3.69"),
            }

    @classmethod
    def get_fees(cls) -> Dict[str, Decimal]:
        """Get current fees from EasyCard settings.

        Returns:
            Dict mapping fee types to amounts.
        """
        cache_key = f"{EASYCARD_CACHE_PREFIX}fees"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            from ..models import EasyCardAdminSettings

            fees = {}
            settings = EasyCardAdminSettings.objects.filter(category="fees")
            for setting in settings:
                fees[setting.key] = setting.value

            cache.set(cache_key, fees, timeout=EASYCARD_SETTINGS_CACHE_TTL)
            return fees

        except Exception as e:
            logger.error(f"[EASYCARD] Error fetching fees: {e}")
            return {}

    @classmethod
    def invalidate_user_cache(cls, phone_number: str) -> None:
        """Invalidate cache for a specific user.

        Args:
            phone_number: User's phone number
        """
        normalized_phone = cls._normalize_phone(phone_number)
        cache_key = f"{EASYCARD_CACHE_PREFIX}user_{normalized_phone}"
        cache.delete(cache_key)
        logger.debug(f"[EASYCARD] Cache invalidated for {cls._mask_phone(normalized_phone)}")

    @classmethod
    def invalidate_settings_cache(cls) -> None:
        """Invalidate cached settings (rates, fees)."""
        cache.delete(f"{EASYCARD_CACHE_PREFIX}exchange_rates")
        cache.delete(f"{EASYCARD_CACHE_PREFIX}fees")
        logger.info("[EASYCARD] Settings cache invalidated")

    @classmethod
    def get_profile_by_user_id(cls, user_id: str):
        """Get EasyCard profile by user_id UUID.

        Used by webhook handlers to look up user information
        when receiving transaction events.

        Args:
            user_id: EasyCard user_id (UUID string)

        Returns:
            EasyCardProfile instance or None if not found
        """
        try:
            from ..models import EasyCardProfile
            return EasyCardProfile.objects.filter(user_id=user_id).first()
        except Exception as e:
            logger.error(f"[EASYCARD] Error fetching profile by user_id: {e}")
            return None

    @classmethod
    def get_profile_by_apofiz_id(cls, apofiz_user_id: int):
        """Get EasyCard profile by Apofiz user ID.

        Primary method for looking up EasyCard profiles when
        you have the Apofiz user ID (e.g., from auth token).

        Args:
            apofiz_user_id: User ID from Apofiz backend (integer)

        Returns:
            EasyCardProfile instance or None if not found
        """
        try:
            from ..models import EasyCardProfile
            return EasyCardProfile.objects.filter(apofiz_user_id=apofiz_user_id).first()
        except Exception as e:
            logger.error(f"[EASYCARD] Error fetching profile by apofiz_user_id: {e}")
            return None

    @classmethod
    def get_phone_by_user_id(cls, user_id: str) -> Optional[str]:
        """Get user's phone number by EasyCard user_id.

        Convenience method for webhook handlers that only need
        the phone number.

        Args:
            user_id: EasyCard user_id (UUID string)

        Returns:
            Phone number string or None if not found
        """
        profile = cls.get_profile_by_user_id(user_id)
        return profile.phone if profile else None

    @classmethod
    def get_phone_by_apofiz_id(cls, apofiz_user_id: int) -> Optional[str]:
        """Get user's phone number by Apofiz user ID.

        Args:
            apofiz_user_id: User ID from Apofiz backend

        Returns:
            Phone number string or None if not found
        """
        profile = cls.get_profile_by_apofiz_id(apofiz_user_id)
        return profile.phone if profile else None

    @classmethod
    def get_user_financial_data_by_apofiz_id(
        cls,
        apofiz_user_id: int,
        include_transactions: bool = True,
        transaction_limit: int = 10,
    ) -> UserFinancialData:
        """Get user's financial data by Apofiz user ID.

        Primary method for getting financial context when
        you have the Apofiz user ID.

        Args:
            apofiz_user_id: User ID from Apofiz backend
            include_transactions: Whether to include recent transactions
            transaction_limit: Max number of transactions to fetch

        Returns:
            UserFinancialData object with all available information
        """
        profile = cls.get_profile_by_apofiz_id(apofiz_user_id)
        if not profile:
            return cls._empty_user_data(f"apofiz:{apofiz_user_id}")

        # Now fetch cards and transactions using the EasyCard user_id
        return cls._fetch_user_data_by_profile(
            profile, include_transactions, transaction_limit
        )

    @classmethod
    def _fetch_user_data_by_profile(
        cls, profile, include_transactions: bool, transaction_limit: int
    ) -> UserFinancialData:
        """Fetch user data using an existing profile."""
        from ..models import EasyCardCard, EasyCardTransaction

        # Get user's cards
        cards = list(
            EasyCardCard.objects.filter(user_id=profile.user_id).values(
                "id",
                "name",
                "type",
                "status",
                "balance",
                "last_four_digits",
                "expiry_date",
            )
        )

        # Calculate total balance
        total_balance = sum(
            card["balance"] for card in cards if card["status"] == "active"
        )

        has_active_card = any(card["status"] == "active" for card in cards)

        # Get recent transactions
        transactions = []
        if include_transactions:
            transactions = list(
                EasyCardTransaction.objects.filter(user_id=profile.user_id)
                .order_by("-created_at")[:transaction_limit]
                .values(
                    "id",
                    "type",
                    "status",
                    "amount",
                    "currency",
                    "fee",
                    "merchant_name",
                    "description",
                    "created_at",
                )
            )

        return UserFinancialData(
            phone=profile.phone or "",
            user_id=str(profile.user_id),
            full_name=profile.display_name,
            total_balance=Decimal(str(total_balance)),
            cards=cards,
            recent_transactions=transactions,
            has_active_card=has_active_card,
            is_registered=True,
        )

    @classmethod
    def _normalize_phone(cls, phone: str) -> str:
        """Normalize phone number format."""
        # Remove all non-digit characters except +
        cleaned = "".join(c for c in phone if c.isdigit() or c == "+")
        # Ensure + prefix
        if not cleaned.startswith("+"):
            cleaned = f"+{cleaned}"
        return cleaned

    @classmethod
    def _mask_phone(cls, phone: str) -> str:
        """Mask phone number for logging."""
        if len(phone) > 7:
            return phone[:7] + "***"
        return phone

    @classmethod
    def _empty_user_data(cls, phone: str) -> UserFinancialData:
        """Return empty user data for unregistered users."""
        return UserFinancialData(
            phone=phone,
            user_id=None,
            full_name="Unknown",
            total_balance=Decimal("0"),
            cards=[],
            recent_transactions=[],
            has_active_card=False,
            is_registered=False,
        )
