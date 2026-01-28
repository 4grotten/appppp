import logging
import json
import re
from typing import Optional, List, Dict, Any, Tuple
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from messenger_bots.models import TelegramBot, BotChat, BotMessage, BotPlatform
from messenger_bots.services.telegram_http_client import telegram_post, get_telegram_session

logger = logging.getLogger(__name__)

# Product pagination settings
PRODUCTS_PER_PAGE = 3
PRODUCTS_CACHE_TIMEOUT = 600  # 10 minutes
MESSAGE_DELAY = 0.5  # seconds between messages (rate limit protection)

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
    CALLBACK_MORE_PRODUCTS = "more_products:"

    def __init__(self, telegram_bot: TelegramBot):
        self.bot = telegram_bot
        self.token = telegram_bot.bot_token

    def _make_request(self, method: str, data: dict = None) -> dict:
        """Make a request to Telegram Bot API using shared connection pool.

        Uses telegram_post() which provides:
        - Connection pooling
        - Automatic retries on 429/502/503/504
        - Default timeout
        """
        url = self.BASE_URL.format(token=self.token, method=method)
        logger.debug(f"[TG_SERVICE] API call: {method}, data={json.dumps(data, ensure_ascii=False)[:200] if data else 'None'}")
        try:
            response = telegram_post(url, json=data)
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
        except Exception as e:
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

    # --- Bot Settings (Telegram API) ---

    def _make_file_request(self, method: str, files: dict, data: dict = None) -> dict:
        """Make a multipart/form-data request to Telegram Bot API (for file uploads).

        Uses shared connection pool with longer timeout for file uploads.
        """
        url = self.BASE_URL.format(token=self.token, method=method)
        logger.debug(f"[TG_SERVICE] File API call: {method}")
        try:
            response = telegram_post(url, data=data, files=files, timeout=(5, 60))
            result = response.json()
            if not result.get("ok"):
                error_msg = result.get("description", "Unknown error")
                logger.error(f"[TG_SERVICE] File API ERROR: method={method}, msg={error_msg}")
            else:
                logger.info(f"[TG_SERVICE] File API SUCCESS: {method}")
            return result
        except Exception as e:
            logger.error(f"[TG_SERVICE] File REQUEST EXCEPTION: method={method}, error={e}", exc_info=True)
            return {"ok": False, "description": str(e)}

    def set_my_name(self, name: str) -> dict:
        """Set bot's name via Telegram API (setMyName). Max 64 chars."""
        result = self._make_request("setMyName", {"name": name})
        if result.get("ok"):
            logger.info(f"[TG_SERVICE] Bot name updated to: '{name}'")
        return result

    def set_my_description(self, description: str) -> dict:
        """Set bot's description via Telegram API (setMyDescription). Max 512 chars."""
        result = self._make_request("setMyDescription", {"description": description})
        if result.get("ok"):
            logger.info(f"[TG_SERVICE] Bot description updated")
        return result

    def set_my_photo(self, photo_file) -> dict:
        """
        Set bot's profile photo via BotFather userbot.

        NOTE: Telegram Bot API does NOT have setMyPhoto method.
        Bot photos can only be changed via BotFather.
        This method uses a userbot to send /setuserpic command to BotFather.

        Accepts file object.
        """
        # Get filename and content type from uploaded file
        filename = getattr(photo_file, 'name', 'photo.jpg')
        content_type = getattr(photo_file, 'content_type', 'image/jpeg')

        # Read file content
        photo_file.seek(0)
        content = photo_file.read()
        logger.info(f"[TG_SERVICE] Photo upload via userbot: filename={filename}, size={len(content)}, content_type={content_type}")
        logger.debug(f"[TG_SERVICE] Photo first 20 bytes: {content[:20]}")

        # Validate
        if len(content) < 100:
            logger.error(f"[TG_SERVICE] Photo too small ({len(content)} bytes)")
            return {"ok": False, "description": f"Photo too small ({len(content)} bytes). Send a real image file."}

        # Get bot username
        if not self.bot.bot_username:
            # Try to fetch it
            me = self.get_me()
            if not me or not self.bot.bot_username:
                return {"ok": False, "description": "Cannot determine bot username. Please configure the bot first."}

        # Use userbot task to set photo via BotFather
        from messenger_bots.tasks import userbot_set_bot_photo_task

        try:
            task = userbot_set_bot_photo_task.delay(
                self.bot.bot_username,
                content,
                content_type
            )
            # Wait for result with timeout
            result = task.get(timeout=90)

            if result.get("success"):
                logger.info(f"[TG_SERVICE] Bot photo updated via BotFather")
                return {"ok": True, "description": "Photo updated via BotFather"}
            else:
                error = result.get("error", "Unknown error")
                logger.error(f"[TG_SERVICE] Failed to set photo via BotFather: {error}")
                return {"ok": False, "description": error}

        except Exception as e:
            logger.error(f"[TG_SERVICE] Userbot task failed: {e}")
            return {"ok": False, "description": f"Failed to set photo via BotFather: {str(e)}"}

    def set_my_photo_from_url(self, photo_url: str) -> dict:
        """Download image from URL and set as bot's profile photo via BotFather."""
        import requests as req
        from urllib.parse import urlparse

        logger.info(f"[TG_SERVICE] Downloading photo from URL: {photo_url}")

        try:
            # Download the image
            response = req.get(photo_url, timeout=30)
            response.raise_for_status()

            content = response.content
            content_type = response.headers.get('Content-Type', 'image/jpeg')

            # Extract filename from URL
            parsed_url = urlparse(photo_url)
            filename = parsed_url.path.split('/')[-1] or 'photo.jpg'

            logger.info(f"[TG_SERVICE] Downloaded photo: filename={filename}, size={len(content)}, content_type={content_type}")

            # Validate
            if len(content) < 100:
                logger.error(f"[TG_SERVICE] Downloaded photo too small ({len(content)} bytes)")
                return {"ok": False, "description": f"Downloaded photo too small ({len(content)} bytes)"}

            if 'image/' not in content_type:
                logger.error(f"[TG_SERVICE] Invalid content type: {content_type}")
                return {"ok": False, "description": f"Invalid content type: {content_type}. Expected image."}

            # Get bot username
            if not self.bot.bot_username:
                me = self.get_me()
                if not me or not self.bot.bot_username:
                    return {"ok": False, "description": "Cannot determine bot username"}

            # Use userbot task to set photo via BotFather
            from messenger_bots.tasks import userbot_set_bot_photo_task

            task = userbot_set_bot_photo_task.delay(
                self.bot.bot_username,
                content,
                content_type
            )
            result = task.get(timeout=90)

            if result.get("success"):
                logger.info(f"[TG_SERVICE] Bot photo updated from URL via BotFather")
                return {"ok": True, "description": "Photo updated via BotFather"}
            else:
                error = result.get("error", "Unknown error")
                logger.error(f"[TG_SERVICE] Failed to set photo from URL: {error}")
                return {"ok": False, "description": error}

        except req.RequestException as e:
            logger.error(f"[TG_SERVICE] Failed to download photo from URL: {e}")
            return {"ok": False, "description": f"Failed to download photo: {str(e)}"}
        except Exception as e:
            logger.error(f"[TG_SERVICE] Userbot task failed: {e}")
            return {"ok": False, "description": f"Failed to set photo via BotFather: {str(e)}"}

    def delete_my_photo(self) -> dict:
        """
        Delete bot's profile photo.

        NOTE: Telegram Bot API does NOT have deleteMyPhoto method.
        Bot photos can only be deleted via BotFather (/deleteuserpic).
        This is not currently implemented via userbot.
        """
        logger.warning("[TG_SERVICE] delete_my_photo is not available via Bot API. Use BotFather /deleteuserpic command.")
        return {"ok": False, "description": "Bot photo deletion is not available via API. Use BotFather /deleteuserpic command."}

    def get_my_name(self) -> dict:
        """Get bot's name via Telegram API (getMyName)."""
        result = self._make_request("getMyName")
        if result.get("ok"):
            name = result.get("result", {}).get("name", "")
            logger.info(f"[TG_SERVICE] Got bot name: '{name}'")
        return result

    def get_my_description(self) -> dict:
        """Get bot's description via Telegram API (getMyDescription)."""
        result = self._make_request("getMyDescription")
        if result.get("ok"):
            description = result.get("result", {}).get("description", "")
            logger.info(f"[TG_SERVICE] Got bot description: '{description[:50]}...'")
        return result

    def get_my_photo_url(self) -> Optional[str]:
        """Get bot's profile photo URL via Telegram API."""
        try:
            # First get bot's user_id from getMe
            me_result = self._make_request("getMe")
            if not me_result.get("ok"):
                return None

            bot_id = me_result.get("result", {}).get("id")
            if not bot_id:
                return None

            # Get bot's profile photos
            photos_result = self._make_request("getUserProfilePhotos", {"user_id": bot_id, "limit": 1})
            if not photos_result.get("ok"):
                return None

            photos = photos_result.get("result", {}).get("photos", [])
            if not photos:
                logger.info(f"[TG_SERVICE] Bot has no profile photo")
                return None

            # Get the largest photo (last in array)
            photo_sizes = photos[0]
            if not photo_sizes:
                return None

            file_id = photo_sizes[-1].get("file_id")
            if not file_id:
                return None

            # Get file path
            file_result = self._make_request("getFile", {"file_id": file_id})
            if not file_result.get("ok"):
                return None

            file_path = file_result.get("result", {}).get("file_path")
            if not file_path:
                return None

            # Construct download URL
            photo_url = f"https://api.telegram.org/file/bot{self.token}/{file_path}"
            logger.info(f"[TG_SERVICE] Got bot photo URL")
            return photo_url

        except Exception as e:
            logger.warning(f"[TG_SERVICE] Failed to get bot photo: {e}")
            return None

    def get_bot_settings(self) -> dict:
        """Get all bot settings from Telegram API (name, description, username, photo)."""
        settings = {
            "username": self.bot.bot_username,
            "name": None,
            "description": None,
            "photo_url": None,
        }

        # Get name
        name_result = self.get_my_name()
        if name_result.get("ok"):
            settings["name"] = name_result.get("result", {}).get("name", "")

        # Get description
        desc_result = self.get_my_description()
        if desc_result.get("ok"):
            settings["description"] = desc_result.get("result", {}).get("description", "")

        # Get photo
        settings["photo_url"] = self.get_my_photo_url()

        return settings

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

    def get_user_profile_photo_url(self, user_id: str, org_id: int) -> Optional[str]:
        """
        Get user's profile photo URL.
        Downloads the photo and saves it to Django storage to avoid token exposure.
        """
        try:
            # Get user profile photos
            result = self._make_request("getUserProfilePhotos", {"user_id": user_id, "limit": 1})
            if not result.get("ok"):
                return None

            photos = result.get("result", {}).get("photos", [])
            if not photos:
                return None

            # Get the largest photo (last in the array for better quality)
            photo_sizes = photos[0]
            if not photo_sizes:
                return None

            # Get file_id from the largest photo size
            file_id = photo_sizes[-1].get("file_id")
            if not file_id:
                return None

            # Get file path from Telegram
            file_result = self._make_request("getFile", {"file_id": file_id})
            if not file_result.get("ok"):
                return None

            file_path = file_result.get("result", {}).get("file_path")
            if not file_path:
                return None

            # Download and save to storage
            return self._download_and_save_photo(user_id, org_id, file_path)

        except Exception as e:
            logger.warning(f"[TG_SERVICE] Failed to get user profile photo: {e}")
            return None

    def _download_and_save_photo(self, user_id: str, org_id: int, telegram_file_path: str) -> Optional[str]:
        """Download photo from Telegram and save to Django storage.

        Uses shared connection pool for file download.
        """
        try:
            from django.core.files.base import ContentFile
            from django.core.files.storage import default_storage

            # Download photo from Telegram using shared session
            download_url = f"https://api.telegram.org/file/bot{self.token}/{telegram_file_path}"
            session = get_telegram_session()
            response = session.get(download_url, timeout=(5, 30))

            if response.status_code != 200:
                logger.warning(f"[TG_SERVICE] Failed to download photo: HTTP {response.status_code}")
                return None

            # Determine file extension
            ext = telegram_file_path.split(".")[-1] if "." in telegram_file_path else "jpg"

            # Save to storage with organized path
            storage_path = f"bot_user_photos/org_{org_id}/user_{user_id}.{ext}"

            # Delete old photo if exists
            if default_storage.exists(storage_path):
                default_storage.delete(storage_path)

            # Save new photo
            content_file = ContentFile(response.content)
            default_storage.save(storage_path, content_file)

            # Return permanent URL
            return default_storage.url(storage_path)

        except Exception as e:
            logger.warning(f"[TG_SERVICE] Failed to download/save user photo: {e}")
            return None

    # ============== Product Parsing & Pagination ==============

    # Product validation pattern
    PRODUCT_PATTERN = re.compile(
        r'((?:Товар|Product):.*?(?:Ссылка|Link):\s*https?://[^\s]+)',
        re.DOTALL | re.IGNORECASE
    )
    # Footer pattern
    FOOTER_PATTERN = re.compile(
        r'((?:Больше товаров|More products).+)$',
        re.DOTALL | re.IGNORECASE
    )
    # AI separator
    AI_SEPARATOR = "###NEXT###"

    @classmethod
    def parse_products_from_response(cls, ai_response: str) -> Tuple[List[str], str]:
        """
        Parse AI response and split into separate product blocks.

        Uses hybrid approach for maximum reliability:
        1. If ###NEXT### separators present - split by them first (faster)
        2. Validate each block with regex (ensures correct format)
        3. Fallback to pure regex if no separators (handles edge cases)

        Supports both Russian and English formats:
        - Russian: Товар: ... Ссылка: URL
        - English: Product: ... Link: URL

        Returns:
            products: list of validated product blocks
            footer: closing text ("Больше товаров..."/"More products...")
        """
        products = []

        # Step 1: Extract footer first (before processing)
        footer = ""
        footer_match = cls.FOOTER_PATTERN.search(ai_response)
        if footer_match:
            footer = footer_match.group(1).strip()
            # Remove ###NEXT### from footer if present
            footer = footer.replace(cls.AI_SEPARATOR, "").strip()

        # Step 2: Clean response - remove footer from parsing
        clean_response = ai_response
        if footer:
            clean_response = ai_response[:ai_response.rfind(footer)].strip()

        # Step 3: Hybrid parsing approach
        if cls.AI_SEPARATOR in clean_response:
            # Fast path: split by ###NEXT### and validate each block
            logger.debug("[TG_SERVICE] Using ###NEXT### separator parsing")
            blocks = clean_response.split(cls.AI_SEPARATOR)

            for block in blocks:
                block = block.strip()
                if not block:
                    continue

                # Validate block has correct product format
                match = cls.PRODUCT_PATTERN.search(block)
                if match:
                    products.append(match.group(1).strip())
        else:
            # Fallback: pure regex parsing (handles any format)
            logger.debug("[TG_SERVICE] Using regex-only parsing")
            matches = cls.PRODUCT_PATTERN.findall(clean_response)
            products = [m.strip() for m in matches if m.strip()]

        # Step 4: Deduplicate while preserving order
        seen = set()
        unique_products = []
        for p in products:
            if p not in seen:
                seen.add(p)
                unique_products.append(p)

        logger.debug(f"[TG_SERVICE] Parsed {len(unique_products)} products, footer: {bool(footer)}")
        return unique_products, footer

    @staticmethod
    def send_products_async(
        telegram_bot_id: int,
        chat_id: int,
        products: List[str],
        footer: str,
        page: int = 0,
        language: str = "ru",
    ):
        """
        Send products with pagination asynchronously via Celery task.
        This avoids blocking the webhook response.
        """
        from messenger_bots.tasks import send_telegram_products_task

        send_telegram_products_task.delay(
            telegram_bot_id=telegram_bot_id,
            chat_id=chat_id,
            products=products,
            footer=footer,
            page=page,
            language=language,
        )

    @staticmethod
    def cache_products(chat_id: str, products: List[str], footer: str):
        """Cache products for pagination."""
        cache_key = f"tg_products:{chat_id}"
        cache.set(cache_key, {"products": products, "footer": footer}, timeout=PRODUCTS_CACHE_TIMEOUT)

    @staticmethod
    def get_cached_products(chat_id: str) -> Tuple[List[str], str]:
        """Get cached products for pagination."""
        cache_key = f"tg_products:{chat_id}"
        data = cache.get(cache_key)
        if data:
            return data.get("products", []), data.get("footer", "")
        return [], ""

    # ============== Inline Keyboard Builders ==============

    def build_main_menu_keyboard(self, language: str = "ru") -> dict:
        """Build main menu inline keyboard."""
        from messenger_bots.services.assistant import BotAssistantService

        return {
            "inline_keyboard": [
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
            "text": back_text.get(language, back_text["ru"]),
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
            "text": back_text.get(language, back_text["ru"]),
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

        # Update user_name and fetch user_photo if needed
        update_fields = []
        if not created and chat.user_name != user_name:
            chat.user_name = user_name
            update_fields.append("user_name")

        # Fetch user photo if not already set or on new chat
        if created or not chat.user_photo:
            service = cls(telegram_bot)
            user_photo_url = service.get_user_profile_photo_url(user_id, telegram_bot.organization_id)
            if user_photo_url:
                chat.user_photo = user_photo_url
                update_fields.append("user_photo")
                logger.debug(f"[TG_SERVICE] User photo saved: {user_photo_url[:60]}...")

        if update_fields:
            chat.save(update_fields=update_fields)

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

        # Sync with organizations.Chat for unified chat list
        cls._sync_linked_chat(chat, telegram_bot.organization)

        # Send WebSocket notification for incoming message
        cls._send_ws_notification(incoming_msg, chat)

        # Handle /start command
        service = cls(telegram_bot)
        if text.strip().lower() == "/start":
            logger.info(f"[TG_SERVICE] Handling /start command")
            welcome_text = BotAssistantService._get_message("welcome", user_language)
            keyboard = service.build_main_menu_keyboard(user_language)
            result = service.send_message(chat_id, welcome_text, reply_markup=keyboard)
            if result:
                start_response_msg = BotMessage.objects.create(
                    chat=chat,
                    sender=BotMessage.ASSISTANT,
                    text=welcome_text,
                    platform_message_id=str(result.get("message_id", "")),
                )
                cls._send_ws_notification(start_response_msg, chat)
                logger.info(f"[TG_SERVICE] /start response sent successfully")
            else:
                logger.error(f"[TG_SERVICE] Failed to send /start response")
            return welcome_text

        # Check if AI is enabled for this bot
        if not telegram_bot.is_ai_enabled:
            logger.info(f"[TG_SERVICE] AI disabled for org {telegram_bot.organization_id}, skipping response")
            return None

        # Check if organization subscription is active
        from messenger_bots.services.subscription_check import check_subscription_active
        if not check_subscription_active(telegram_bot.organization):
            logger.info(f"[TG_SERVICE] Subscription expired for org {telegram_bot.organization_id}, skipping AI response")
            return None

        # Get chat history for context (use bot's configured limit or default)
        context_limit = getattr(telegram_bot, 'context_messages_limit', CHAT_HISTORY_LIMIT)
        chat_history = cls._get_chat_history(chat, limit=context_limit)
        logger.debug(f"[TG_SERVICE] Chat history: {len(chat_history)} messages (limit={context_limit})")

        # Send typing indicator BEFORE AI call so user sees bot is "thinking"
        service = cls(telegram_bot)
        service.send_typing_action(chat_id)

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

        # Check if response contains multiple products for pagination
        products, footer = cls.parse_products_from_response(response_text)

        if len(products) > PRODUCTS_PER_PAGE:
            # Cache products for pagination and send first batch asynchronously
            logger.info(f"[TG_SERVICE] Found {len(products)} products, using pagination")
            cls.cache_products(chat_id, products, footer)
            cls.send_products_async(
                telegram_bot_id=telegram_bot.id,
                chat_id=chat.id,
                products=products,
                footer=footer,
                page=0,
                language=user_language,
            )
        elif products:
            # Few products (1-3): send each as separate message without pagination
            logger.info(f"[TG_SERVICE] Found {len(products)} products, sending individually")
            keyboard = service.build_main_menu_keyboard(user_language)

            # Send each product as separate message and save each to DB
            for i, product in enumerate(products):
                is_last = (i == len(products) - 1) and not footer
                result = service.send_message(
                    chat_id,
                    product,
                    message_id if i == 0 else None,
                    reply_markup=keyboard if is_last else None
                )
                # Save each product as separate message
                if result:
                    product_msg = BotMessage.objects.create(
                        chat=chat,
                        sender=BotMessage.ASSISTANT,
                        text=product,
                        platform_message_id=str(result.get("message_id", "")),
                    )
                    cls._send_ws_notification(product_msg, chat)

            # Send footer with keyboard
            if footer:
                result = service.send_message(chat_id, footer, reply_markup=keyboard)
                if result:
                    footer_msg = BotMessage.objects.create(
                        chat=chat,
                        sender=BotMessage.ASSISTANT,
                        text=footer,
                        platform_message_id=str(result.get("message_id", "")),
                    )
                    cls._send_ws_notification(footer_msg, chat)
            logger.info(f"[TG_SERVICE] {len(products)} products sent individually")
        else:
            # No products - send regular response (clean ###NEXT### just in case)
            clean_response = response_text.replace(cls.AI_SEPARATOR, "").strip()
            keyboard = service.build_main_menu_keyboard(user_language)
            result = service.send_message(chat_id, clean_response, message_id, reply_markup=keyboard)

            # Save assistant response
            if result:
                outgoing_msg = BotMessage.objects.create(
                    chat=chat,
                    sender=BotMessage.ASSISTANT,
                    text=clean_response,
                    platform_message_id=str(result.get("message_id", "")),
                )
                cls._send_ws_notification(outgoing_msg, chat)
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

        elif data.startswith(cls.CALLBACK_MORE_PRODUCTS):
            # Handle "Show more" products pagination
            page = int(data.replace(cls.CALLBACK_MORE_PRODUCTS, ""))
            return cls._show_more_products(service, telegram_bot, chat_id, message_id, page, user_language)

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
            from shop.models import ItemSubcategory

            categories = ItemSubcategory.objects.filter(
                organization=telegram_bot.organization,
            ).values("id", "name")[:10]

            # Rename 'name' to 'title' for keyboard compatibility
            categories_list = [{"id": c["id"], "title": c["name"]} for c in categories]

            if not categories_list:
                # No categories, show products directly
                return cls._show_all_products(service, telegram_bot, chat_id, message_id, language)

            # Build categories text
            text_templates = {"ru": "Выберите категорию:", "en": "Select a category:"}
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
                is_published=True,
                removed_at__isnull=True,
            ).values("id", "name", "price")[:10]

            # Rename 'name' to 'title' for keyboard compatibility
            products_list = [{"id": p["id"], "title": p["name"], "price": p["price"]} for p in products]

            if not products_list:
                from messenger_bots.services.assistant import BotAssistantService
                text = BotAssistantService._get_message("no_products", language)
                keyboard = service.build_main_menu_keyboard(language)
                service.edit_message_text(chat_id, message_id, text, reply_markup=keyboard)
                return text

            text_templates = {"ru": "Наши товары:", "en": "Our products:"}
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
        """Show products in a category (subcategory)."""
        try:
            from shop.models import ShopItem, ItemSubcategory

            category = ItemSubcategory.objects.filter(id=category_id).first()
            category_name = category.name if category else ""

            products = ShopItem.objects.filter(
                organization=telegram_bot.organization,
                subcategory_id=category_id,
                is_published=True,
                removed_at__isnull=True,
            ).values("id", "name", "price")[:10]

            # Rename 'name' to 'title' for keyboard compatibility
            products_list = [{"id": p["id"], "title": p["name"], "price": p["price"]} for p in products]

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
            ).select_related("subcategory").prefetch_related("images").first()

            if not product:
                return ""

            # Build product description
            currency = telegram_bot.organization.currency_id or ""
            price_str = f"<b>{product.price} {currency}</b>" if product.price else ""

            text = f"<b>{product.name}</b>\n\n"
            if product.description:
                text += f"{product.description}\n\n"
            if price_str:
                text += f"Цена: {price_str}"

            # Back button
            back_text = {"ru": "« Назад к товарам", "en": "« Back to products"}
            keyboard = {
                "inline_keyboard": [[{
                    "text": back_text.get(language, back_text["ru"]),
                    "callback_data": f"{cls.CALLBACK_CATEGORY}{product.subcategory_id}" if product.subcategory_id else cls.CALLBACK_CATALOG,
                }]]
            }

            # Send photo if available (images is ManyToMany)
            first_image = product.images.first()
            if first_image:
                # Get image URL
                image_url = first_image.file.url if hasattr(first_image, 'file') and first_image.file else None
                if image_url:
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
            text_parts.append(f"📍 <b>{address_label.get(language, address_label['ru'])}:</b> {org.address}")

        # Working hours
        if org.opens_at or org.closes_at:
            hours_label = {"ru": "Часы работы", "en": "Working hours"}
            opens = str(org.opens_at)[:5] if org.opens_at else "—"
            closes = str(org.closes_at)[:5] if org.closes_at else "—"
            text_parts.append(f"🕐 <b>{hours_label.get(language, hours_label['ru'])}:</b> {opens} - {closes}")

        # Phone numbers
        phone_numbers = list(org.phone_numbers.values_list("phone_number", flat=True))
        if phone_numbers:
            phone_label = {"ru": "Телефоны", "en": "Phones"}
            phones_str = "\n".join([f"📞 {phone}" for phone in phone_numbers])
            text_parts.append(f"\n<b>{phone_label.get(language, phone_label['ru'])}:</b>\n{phones_str}")

        # Social contacts
        social_contacts = list(org.social_contacts.values_list("url", flat=True))
        if social_contacts:
            social_label = {"ru": "Соц. сети", "en": "Social media"}
            socials_str = "\n".join([f"🔗 {url}" for url in social_contacts[:5]])
            text_parts.append(f"\n<b>{social_label.get(language, social_label['ru'])}:</b>\n{socials_str}")

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
    def _show_more_products(
        cls,
        service: "TelegramBotService",
        telegram_bot: TelegramBot,
        chat_id: str,
        message_id: str,
        page: int,
        language: str,
    ) -> str:
        """Handle 'Show more' products pagination callback."""
        try:
            # Get cached products
            products, footer = cls.get_cached_products(chat_id)
            if not products:
                logger.warning(f"[TG_SERVICE] No cached products for chat_id={chat_id}")
                return ""

            # Delete the "Show more" button message
            service._make_request("deleteMessage", {"chat_id": chat_id, "message_id": message_id})

            # Get chat for saving messages
            chat = BotChat.objects.filter(
                organization=telegram_bot.organization,
                platform=BotPlatform.TELEGRAM,
                platform_chat_id=chat_id,
            ).first()

            if not chat:
                logger.error(f"[TG_SERVICE] Chat not found for chat_id={chat_id}")
                return ""

            # Send next batch asynchronously
            cls.send_products_async(
                telegram_bot_id=telegram_bot.id,
                chat_id=chat.id,
                products=products,
                footer=footer,
                page=page,
                language=language,
            )
            return f"Showing page {page + 1}"

        except Exception as e:
            logger.error(f"[TG_SERVICE] Error showing more products: {e}", exc_info=True)
            return ""

    @classmethod
    def _sync_linked_chat(cls, bot_chat: BotChat, organization) -> None:
        """
        Sync BotChat with organizations.Chat for unified chat list.
        Creates or updates the linked Chat and increments unread_count.
        Uses F() for atomic increment to avoid race conditions.
        """
        from django.db.models import F
        from organizations.models import Assistant, Chat, ChatSource

        try:
            # Get assistant for this organization
            assistant = Assistant.objects.filter(organization=organization).first()
            if not assistant:
                logger.warning(f"[TG_SERVICE] No assistant found for org_id={organization.id}")
                return

            # Get or create linked Chat
            linked_chat, created = Chat.objects.get_or_create(
                bot_chat=bot_chat,
                defaults={
                    'assistant': assistant,
                    'source': ChatSource.TELEGRAM,
                    'user': None,
                    'is_read': False,
                    'unread_count': 1,
                }
            )

            if created:
                logger.info(f"[TG_SERVICE] Created linked Chat id={linked_chat.id} for BotChat id={bot_chat.id}")
            else:
                # Increment unread_count atomically and mark as unread
                Chat.objects.filter(id=linked_chat.id).update(
                    unread_count=F('unread_count') + 1,
                    is_read=False
                )
                logger.debug(f"[TG_SERVICE] Updated linked Chat id={linked_chat.id}, incremented unread_count")

        except Exception as e:
            logger.error(f"[TG_SERVICE] Error syncing linked chat: {e}", exc_info=True)

    @classmethod
    def _send_ws_notification(cls, bot_message: BotMessage, bot_chat: BotChat) -> None:
        """
        Send WebSocket notification for new Telegram message.
        Uses the same format as web chat messages for frontend compatibility.
        """
        from shop.serializers.comment_serializers import BotMessageSerializer

        try:
            # Get linked Chat id
            linked_chat = getattr(bot_chat, 'linked_chat', None)
            if not linked_chat:
                logger.debug(f"[TG_SERVICE] No linked chat for BotChat id={bot_chat.id}, skipping WS")
                return

            chat_group_name = f"chat_{linked_chat.id}"

            # Serialize message using BotMessageSerializer (unified format)
            serialized_data = BotMessageSerializer(bot_message).data

            # Send via channel layer
            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    chat_group_name,
                    {
                        "type": "chat_message",
                        "message": serialized_data,
                    }
                )
                logger.debug(f"[TG_SERVICE] WS notification sent to {chat_group_name}")
            else:
                logger.warning(f"[TG_SERVICE] No channel layer available for WS notification")

        except Exception as e:
            logger.error(f"[TG_SERVICE] Error sending WS notification: {e}", exc_info=True)

    @classmethod
    def _get_chat_history(cls, chat: BotChat, limit: int = None) -> List[Dict[str, str]]:
        """
        Get last N messages from chat for context.

        Args:
            chat: BotChat instance
            limit: Number of message pairs (user+assistant) to include.
                   Default is CHAT_HISTORY_LIMIT (5).
        """
        if limit is None:
            limit = CHAT_HISTORY_LIMIT

        # Ensure limit is within reasonable bounds (1-20 pairs)
        limit = max(1, min(limit, 20))

        messages = BotMessage.objects.filter(chat=chat).order_by("-created_at")[:limit * 2]

        # Convert to list and reverse (oldest first)
        messages_list = list(messages)[::-1]

        history = []
        for msg in messages_list:
            role = "user" if msg.sender == BotMessage.USER else "assistant"
            history.append({
                "role": role,
                "content": msg.text,
            })

        return history[-limit * 2:]

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
