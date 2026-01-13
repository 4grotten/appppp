import logging
import json
import requests
from typing import Optional, List, Dict, Any
from django.conf import settings
from django.utils import timezone

from messenger_bots.models import TelegramBot, BotChat, BotMessage, BotPlatform

logger = logging.getLogger(__name__)

# Chat history limit for context
CHAT_HISTORY_LIMIT = 5


class TelegramBotService:
    """Service for interacting with Telegram Bot API."""

    BASE_URL = "https://api.telegram.org/bot{token}/{method}"

    # Callback data prefixes for inline buttons
    CALLBACK_CATALOG = "catalog"
    CALLBACK_CONTACTS = "contacts"
    CALLBACK_CATEGORY = "cat_"
    CALLBACK_PRODUCT = "prod_"
    CALLBACK_BACK = "back"

    def __init__(self, telegram_bot: TelegramBot):
        self.bot = telegram_bot
        self.token = telegram_bot.bot_token

    def _make_request(self, method: str, data: dict = None) -> dict:
        """Make a request to Telegram Bot API."""
        url = self.BASE_URL.format(token=self.token, method=method)
        logger.debug(f"[TG_SERVICE] API call: {method}, data={json.dumps(data, ensure_ascii=False)[:200] if data else 'None'}")
        try:
            response = requests.post(url, json=data, timeout=30)
            result = response.json()
            if not result.get("ok"):
                error_msg = result.get("description", "Unknown error")
                error_code = result.get("error_code", "N/A")
                logger.error(f"[TG_SERVICE] API ERROR: method={method}, code={error_code}, msg={error_msg}")
                self.bot.last_error = error_msg
                self.bot.save(update_fields=["last_error"])
            else:
                logger.debug(f"[TG_SERVICE] API SUCCESS: {method}")
            return result
        except requests.RequestException as e:
            logger.error(f"[TG_SERVICE] REQUEST EXCEPTION: method={method}, error={e}", exc_info=True)
            self.bot.last_error = str(e)
            self.bot.save(update_fields=["last_error"])
            return {"ok": False, "description": str(e)}

    def get_me(self) -> Optional[dict]:
        """Get bot information."""
        result = self._make_request("getMe")
        if result.get("ok"):
            bot_info = result.get("result", {})
            self.bot.bot_username = bot_info.get("username")
            self.bot.last_error = None
            self.bot.save(update_fields=["bot_username", "last_error"])
            return bot_info
        return None

    def set_webhook(self, webhook_url: str) -> bool:
        """Set webhook URL for receiving updates."""
        data = {
            "url": webhook_url,
            "secret_token": self.bot.webhook_secret,
            "allowed_updates": ["message", "callback_query"],
        }
        result = self._make_request("setWebhook", data)
        if result.get("ok"):
            self.bot.webhook_url = webhook_url
            self.bot.last_error = None
            self.bot.save(update_fields=["webhook_url", "last_error"])
            return True
        return False

    def delete_webhook(self) -> bool:
        """Remove webhook."""
        result = self._make_request("deleteWebhook")
        if result.get("ok"):
            self.bot.webhook_url = None
            self.bot.save(update_fields=["webhook_url"])
            return True
        return False

    def send_message(
        self,
        chat_id: str,
        text: str,
        reply_to_message_id: str = None,
        reply_markup: dict = None,
    ) -> Optional[dict]:
        """Send a text message to a chat."""
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
        }
        if reply_to_message_id:
            data["reply_to_message_id"] = reply_to_message_id
        if reply_markup:
            data["reply_markup"] = json.dumps(reply_markup)

        result = self._make_request("sendMessage", data)
        if result.get("ok"):
            return result.get("result")
        return None

    def send_photo(
        self,
        chat_id: str,
        photo_url: str,
        caption: str = None,
        reply_markup: dict = None,
    ) -> Optional[dict]:
        """Send a photo to a chat."""
        data = {
            "chat_id": chat_id,
            "photo": photo_url,
            "parse_mode": "HTML",
        }
        if caption:
            data["caption"] = caption
        if reply_markup:
            data["reply_markup"] = json.dumps(reply_markup)

        result = self._make_request("sendPhoto", data)
        if result.get("ok"):
            return result.get("result")
        return None

    def edit_message_text(
        self,
        chat_id: str,
        message_id: str,
        text: str,
        reply_markup: dict = None,
    ) -> Optional[dict]:
        """Edit a message text."""
        data = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": "HTML",
        }
        if reply_markup:
            data["reply_markup"] = json.dumps(reply_markup)

        result = self._make_request("editMessageText", data)
        if result.get("ok"):
            return result.get("result")
        return None

    def answer_callback_query(
        self,
        callback_query_id: str,
        text: str = None,
        show_alert: bool = False,
    ) -> bool:
        """Answer a callback query (inline button press)."""
        data = {
            "callback_query_id": callback_query_id,
            "show_alert": show_alert,
        }
        if text:
            data["text"] = text

        result = self._make_request("answerCallbackQuery", data)
        return result.get("ok", False)

    def send_typing_action(self, chat_id: str) -> bool:
        """Send typing indicator."""
        data = {
            "chat_id": chat_id,
            "action": "typing",
        }
        result = self._make_request("sendChatAction", data)
        return result.get("ok", False)

    # ============== Inline Keyboard Builders ==============

    def build_main_menu_keyboard(self, language: str = "ru") -> dict:
        """Build main menu inline keyboard."""
        from messenger_bots.services.assistant import BotAssistantService

        return {
            "inline_keyboard": [
                [
                    {
                        "text": BotAssistantService._get_message("catalog_button", language),
                        "callback_data": self.CALLBACK_CATALOG,
                    },
                ],
                [
                    {
                        "text": BotAssistantService._get_message("contacts_button", language),
                        "callback_data": self.CALLBACK_CONTACTS,
                    },
                ],
            ]
        }

    def build_categories_keyboard(self, categories: List[Dict], language: str = "ru") -> dict:
        """Build categories inline keyboard."""
        buttons = []
        for cat in categories[:10]:  # Limit to 10 categories
            buttons.append([{
                "text": cat["title"],
                "callback_data": f"{self.CALLBACK_CATEGORY}{cat['id']}",
            }])

        # Add back button
        back_text = {"ru": "« Назад", "en": "« Back"}
        buttons.append([{
            "text": back_text.get(language, "« Назад"),
            "callback_data": self.CALLBACK_BACK,
        }])

        return {"inline_keyboard": buttons}

    def build_products_keyboard(self, products: List[Dict], category_id: int, language: str = "ru") -> dict:
        """Build products inline keyboard."""
        buttons = []
        for prod in products[:10]:  # Limit to 10 products
            price_str = f" - {prod['price']}" if prod.get("price") else ""
            buttons.append([{
                "text": f"{prod['title']}{price_str}",
                "callback_data": f"{self.CALLBACK_PRODUCT}{prod['id']}",
            }])

        # Add back button
        back_text = {"ru": "« К категориям", "en": "« Categories"}
        buttons.append([{
            "text": back_text.get(language, "« К категориям"),
            "callback_data": self.CALLBACK_CATALOG,
        }])

        return {"inline_keyboard": buttons}

    @classmethod
    def process_webhook_update(cls, telegram_bot: TelegramBot, update: dict) -> Optional[str]:
        """
        Process incoming webhook update from Telegram.
        Handles both messages and callback queries (inline button presses).
        """
        logger.info(f"[TG_SERVICE] ====== PROCESSING UPDATE ======")
        logger.info(f"[TG_SERVICE] Bot: @{telegram_bot.bot_username}, org_id={telegram_bot.organization_id}")

        # Handle callback query (inline button press)
        callback_query = update.get("callback_query")
        if callback_query:
            logger.info(f"[TG_SERVICE] Update type: CALLBACK_QUERY, data='{callback_query.get('data')}'")
            return cls._handle_callback_query(telegram_bot, callback_query)

        # Handle regular message
        message = update.get("message")
        if not message:
            logger.warning(f"[TG_SERVICE] Update has no message or callback_query, skipping")
            return None

        text = message.get("text", "")[:100]
        logger.info(f"[TG_SERVICE] Update type: MESSAGE, text='{text}'")
        return cls._handle_message(telegram_bot, message)

    @classmethod
    def _handle_message(cls, telegram_bot: TelegramBot, message: dict) -> Optional[str]:
        """Handle incoming text message."""
        chat_id = str(message.get("chat", {}).get("id"))
        user = message.get("from", {})
        user_id = str(user.get("id", ""))
        text = message.get("text", "")
        message_id = str(message.get("message_id", ""))

        logger.info(f"[TG_SERVICE] _handle_message: chat_id={chat_id}, user_id={user_id}, text='{text[:50]}'")

        if not text or not chat_id:
            logger.warning(f"[TG_SERVICE] Empty text or chat_id, skipping")
            return None

        # Detect user language
        from messenger_bots.services.assistant import BotAssistantService
        user_language = BotAssistantService.detect_language_from_telegram(user)
        logger.debug(f"[TG_SERVICE] Detected language: {user_language}")

        # Get or create chat
        user_name = user.get("first_name", "")
        if user.get("last_name"):
            user_name += f" {user.get('last_name')}"
        username = user.get("username")
        if username:
            user_name = f"{user_name} (@{username})"

        chat, created = BotChat.objects.get_or_create(
            organization=telegram_bot.organization,
            platform=BotPlatform.TELEGRAM,
            platform_chat_id=chat_id,
            defaults={
                "platform_user_id": user_id,
                "user_name": user_name,
            }
        )
        logger.info(f"[TG_SERVICE] Chat: id={chat.id}, {'CREATED' if created else 'EXISTS'}, user='{user_name}'")

        if not created and chat.user_name != user_name:
            chat.user_name = user_name
            chat.save(update_fields=["user_name"])

        # Save incoming message
        incoming_msg = BotMessage.objects.create(
            chat=chat,
            sender=BotMessage.USER,
            text=text,
            platform_message_id=message_id,
        )
        logger.info(f"[TG_SERVICE] Saved incoming message: id={incoming_msg.id}")

        # Update last message time
        chat.last_message_at = timezone.now()
        chat.save(update_fields=["last_message_at"])

        # Handle /start command
        service = cls(telegram_bot)
        if text.strip().lower() == "/start":
            logger.info(f"[TG_SERVICE] Handling /start command")
            welcome_text = BotAssistantService._get_message("welcome", user_language)
            keyboard = service.build_main_menu_keyboard(user_language)
            result = service.send_message(chat_id, welcome_text, reply_markup=keyboard)
            if result:
                BotMessage.objects.create(
                    chat=chat,
                    sender=BotMessage.ASSISTANT,
                    text=welcome_text,
                    platform_message_id=str(result.get("message_id", "")),
                )
                logger.info(f"[TG_SERVICE] /start response sent successfully")
            else:
                logger.error(f"[TG_SERVICE] Failed to send /start response")
            return welcome_text

        # Get chat history for context
        chat_history = cls._get_chat_history(chat)
        logger.debug(f"[TG_SERVICE] Chat history: {len(chat_history)} messages")

        # Get AI response with context and language
        logger.info(f"[TG_SERVICE] Requesting AI response...")
        try:
            response_text = BotAssistantService.get_response(
                organization=telegram_bot.organization,
                question=text,
                chat_history=chat_history,
                user_language=user_language,
            )
            logger.info(f"[TG_SERVICE] AI response received: '{response_text[:100]}...'")
        except Exception as e:
            logger.error(f"[TG_SERVICE] ERROR getting AI response: {e}", exc_info=True)
            response_text = BotAssistantService._get_message("error", user_language)

        # Send response with main menu
        service.send_typing_action(chat_id)
        keyboard = service.build_main_menu_keyboard(user_language)
        result = service.send_message(chat_id, response_text, message_id, reply_markup=keyboard)

        # Save assistant response
        if result:
            outgoing_msg = BotMessage.objects.create(
                chat=chat,
                sender=BotMessage.ASSISTANT,
                text=response_text,
                platform_message_id=str(result.get("message_id", "")),
            )
            logger.info(f"[TG_SERVICE] Response sent and saved: msg_id={outgoing_msg.id}")
        else:
            logger.error(f"[TG_SERVICE] Failed to send response to chat_id={chat_id}")

        logger.info(f"[TG_SERVICE] ====== MESSAGE PROCESSED ======")
        return response_text

    @classmethod
    def _handle_callback_query(cls, telegram_bot: TelegramBot, callback_query: dict) -> Optional[str]:
        """Handle callback query from inline button press."""
        callback_id = callback_query.get("id")
        data = callback_query.get("data", "")
        message = callback_query.get("message", {})
        chat_id = str(message.get("chat", {}).get("id"))
        message_id = str(message.get("message_id", ""))
        user = callback_query.get("from", {})

        # Detect user language
        from messenger_bots.services.assistant import BotAssistantService
        user_language = BotAssistantService.detect_language_from_telegram(user)

        service = cls(telegram_bot)

        # Answer callback to remove loading state
        service.answer_callback_query(callback_id)

        # Handle different callbacks
        if data == cls.CALLBACK_CATALOG:
            return cls._show_catalog(service, telegram_bot, chat_id, message_id, user_language)

        elif data == cls.CALLBACK_CONTACTS:
            return cls._show_contacts(service, telegram_bot, chat_id, message_id, user_language)

        elif data.startswith(cls.CALLBACK_CATEGORY):
            category_id = int(data.replace(cls.CALLBACK_CATEGORY, ""))
            return cls._show_category_products(service, telegram_bot, chat_id, message_id, category_id, user_language)

        elif data.startswith(cls.CALLBACK_PRODUCT):
            product_id = int(data.replace(cls.CALLBACK_PRODUCT, ""))
            return cls._show_product(service, telegram_bot, chat_id, product_id, user_language)

        elif data == cls.CALLBACK_BACK:
            # Back to main menu
            welcome_text = BotAssistantService._get_message("welcome", user_language)
            keyboard = service.build_main_menu_keyboard(user_language)
            service.edit_message_text(chat_id, message_id, welcome_text, reply_markup=keyboard)
            return welcome_text

        return None

    @classmethod
    def _show_catalog(
        cls,
        service: "TelegramBotService",
        telegram_bot: TelegramBot,
        chat_id: str,
        message_id: str,
        language: str,
    ) -> str:
        """Show product categories."""
        try:
            from shop.models import Category

            categories = Category.objects.filter(
                organization=telegram_bot.organization,
                is_active=True,
            ).values("id", "title")[:10]

            categories_list = list(categories)

            if not categories_list:
                # No categories, show products directly
                return cls._show_all_products(service, telegram_bot, chat_id, message_id, language)

            # Build categories text
            text_templates = {
                "ru": "Выберите категорию:",
                "en": "Select a category:",
            }
            text = text_templates.get(language, text_templates["ru"])

            keyboard = service.build_categories_keyboard(categories_list, language)
            service.edit_message_text(chat_id, message_id, text, reply_markup=keyboard)
            return text

        except Exception as e:
            logger.error(f"Error showing catalog: {e}")
            return cls._show_all_products(service, telegram_bot, chat_id, message_id, language)

    @classmethod
    def _show_all_products(
        cls,
        service: "TelegramBotService",
        telegram_bot: TelegramBot,
        chat_id: str,
        message_id: str,
        language: str,
    ) -> str:
        """Show all products without categories."""
        try:
            from shop.models import ShopItem

            products = ShopItem.objects.filter(
                organization=telegram_bot.organization,
                is_active=True,
                is_deleted=False,
            ).values("id", "title", "price")[:10]

            products_list = list(products)

            if not products_list:
                from messenger_bots.services.assistant import BotAssistantService
                text = BotAssistantService._get_message("no_products", language)
                keyboard = service.build_main_menu_keyboard(language)
                service.edit_message_text(chat_id, message_id, text, reply_markup=keyboard)
                return text

            text_templates = {
                "ru": "Наши товары:",
                "en": "Our products:",
            }
            text = text_templates.get(language, text_templates["ru"])

            keyboard = service.build_products_keyboard(products_list, 0, language)
            service.edit_message_text(chat_id, message_id, text, reply_markup=keyboard)
            return text

        except Exception as e:
            logger.error(f"Error showing products: {e}")
            return ""

    @classmethod
    def _show_category_products(
        cls,
        service: "TelegramBotService",
        telegram_bot: TelegramBot,
        chat_id: str,
        message_id: str,
        category_id: int,
        language: str,
    ) -> str:
        """Show products in a category."""
        try:
            from shop.models import ShopItem, Category

            category = Category.objects.filter(id=category_id).first()
            category_name = category.title if category else ""

            products = ShopItem.objects.filter(
                organization=telegram_bot.organization,
                category_id=category_id,
                is_active=True,
                is_deleted=False,
            ).values("id", "title", "price")[:10]

            products_list = list(products)

            if not products_list:
                from messenger_bots.services.assistant import BotAssistantService
                text = BotAssistantService._get_message("no_products", language)
                keyboard = service.build_main_menu_keyboard(language)
                service.edit_message_text(chat_id, message_id, text, reply_markup=keyboard)
                return text

            text = f"<b>{category_name}</b>"
            keyboard = service.build_products_keyboard(products_list, category_id, language)
            service.edit_message_text(chat_id, message_id, text, reply_markup=keyboard)
            return text

        except Exception as e:
            logger.error(f"Error showing category products: {e}")
            return ""

    @classmethod
    def _show_product(
        cls,
        service: "TelegramBotService",
        telegram_bot: TelegramBot,
        chat_id: str,
        product_id: int,
        language: str,
    ) -> str:
        """Show product details with photo."""
        try:
            from shop.models import ShopItem

            product = ShopItem.objects.filter(
                id=product_id,
                organization=telegram_bot.organization,
            ).select_related("category").first()

            if not product:
                return ""

            # Build product description
            currency = telegram_bot.organization.currency_id or ""
            price_str = f"<b>{product.price} {currency}</b>" if product.price else ""

            text = f"<b>{product.title}</b>\n\n"
            if product.description:
                text += f"{product.description}\n\n"
            if price_str:
                text += f"Цена: {price_str}"

            # Back button
            back_text = {
                "ru": "« Назад к товарам",
                "en": "« Back to products",
            }
            keyboard = {
                "inline_keyboard": [[{
                    "text": back_text.get(language, back_text["ru"]),
                    "callback_data": f"{cls.CALLBACK_CATEGORY}{product.category_id}" if product.category_id else cls.CALLBACK_CATALOG,
                }]]
            }

            # Send photo if available
            if product.image:
                # Get image URL
                image_url = product.image.url if hasattr(product.image, 'url') else str(product.image)
                if not image_url.startswith("http"):
                    # Construct full URL
                    base_url = getattr(settings, "MEDIA_URL", "/media/")
                    image_url = f"{base_url}{image_url}".replace("//", "/")

                # Try to send photo
                result = service.send_photo(chat_id, image_url, caption=text, reply_markup=keyboard)
                if result:
                    return text

            # Fallback to text message
            service.send_message(chat_id, text, reply_markup=keyboard)
            return text

        except Exception as e:
            logger.error(f"Error showing product: {e}")
            return ""

    @classmethod
    def _show_contacts(
        cls,
        service: "TelegramBotService",
        telegram_bot: TelegramBot,
        chat_id: str,
        message_id: str,
        language: str,
    ) -> str:
        """Show organization contacts, address and working hours."""
        org = telegram_bot.organization

        # Build contacts text
        text_parts = []

        # Organization name
        text_parts.append(f"<b>{org.title}</b>\n")

        # Address
        if org.address:
            address_label = {"ru": "Адрес", "en": "Address"}
            text_parts.append(f"📍 <b>{address_label.get(language, 'Адрес')}:</b> {org.address}")

        # Working hours
        if org.opens_at or org.closes_at:
            hours_label = {"ru": "Часы работы", "en": "Working hours"}
            opens = str(org.opens_at)[:5] if org.opens_at else "—"
            closes = str(org.closes_at)[:5] if org.closes_at else "—"
            text_parts.append(f"🕐 <b>{hours_label.get(language, 'Часы работы')}:</b> {opens} - {closes}")

        # Phone numbers
        phone_numbers = list(org.phone_numbers.values_list("phone_number", flat=True))
        if phone_numbers:
            phone_label = {"ru": "Телефоны", "en": "Phones"}
            phones_str = "\n".join([f"📞 {phone}" for phone in phone_numbers])
            text_parts.append(f"\n<b>{phone_label.get(language, 'Телефоны')}:</b>\n{phones_str}")

        # Social contacts
        social_contacts = list(org.social_contacts.values_list("url", flat=True))
        if social_contacts:
            social_label = {"ru": "Соц. сети", "en": "Social media"}
            socials_str = "\n".join([f"🔗 {url}" for url in social_contacts[:5]])
            text_parts.append(f"\n<b>{social_label.get(language, 'Соц. сети')}:</b>\n{socials_str}")

        text = "\n".join(text_parts)

        # Back button
        back_text = {"ru": "« Назад", "en": "« Back"}
        keyboard = {
            "inline_keyboard": [[{
                "text": back_text.get(language, "« Назад"),
                "callback_data": cls.CALLBACK_BACK,
            }]]
        }

        service.edit_message_text(chat_id, message_id, text, reply_markup=keyboard)
        return text

    @classmethod
    def _get_chat_history(cls, chat: BotChat) -> List[Dict[str, str]]:
        """Get last N messages from chat for context."""
        messages = BotMessage.objects.filter(chat=chat).order_by("-created_at")[:CHAT_HISTORY_LIMIT * 2]

        # Convert to list and reverse (oldest first)
        messages_list = list(messages)[::-1]

        history = []
        for msg in messages_list:
            role = "user" if msg.sender == BotMessage.USER else "assistant"
            history.append({
                "role": role,
                "content": msg.text,
            })

        return history[-CHAT_HISTORY_LIMIT * 2:]  # Last 5 pairs (10 messages)

    @classmethod
    def setup_bot(cls, telegram_bot: TelegramBot, base_url: str) -> bool:
        """Setup bot: verify token and set webhook."""
        logger.info(f"[TG_SERVICE] ====== SETUP BOT ======")
        logger.info(f"[TG_SERVICE] org_id={telegram_bot.organization_id}, base_url={base_url}")
        logger.info(f"[TG_SERVICE] Token: {telegram_bot.bot_token[:20]}...")

        service = cls(telegram_bot)

        # Verify bot token
        logger.info(f"[TG_SERVICE] Step 1: Verifying bot token (getMe)...")
        bot_info = service.get_me()
        if not bot_info:
            logger.error(f"[TG_SERVICE] ERROR: getMe failed - invalid token or API error")
            return False
        logger.info(f"[TG_SERVICE] Bot verified: @{bot_info.get('username')}, id={bot_info.get('id')}")

        # Set webhook with callback query support
        webhook_url = f"{base_url}/api/v1/messenger-bots/telegram/webhook/{telegram_bot.organization_id}/"
        logger.info(f"[TG_SERVICE] Step 2: Setting webhook to: {webhook_url}")

        success = service.set_webhook(webhook_url)
        if success:
            logger.info(f"[TG_SERVICE] SUCCESS: Bot setup complete!")
        else:
            logger.error(f"[TG_SERVICE] ERROR: Failed to set webhook")

        logger.info(f"[TG_SERVICE] ====== SETUP BOT END ======")
        return success
