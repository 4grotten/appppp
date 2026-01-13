from django.test import TestCase
from unittest.mock import patch, MagicMock
import json

from messenger_bots.models import (
    TelegramBot,
    WhatsAppBot,
    BotChat,
    BotMessage,
    BotPlatform,
)
from messenger_bots.services import TelegramBotService, WhatsAppBotService
from organizations.models import Organization, Assistant
from users.models import User


class TelegramBotServiceTest(TestCase):
    """Tests for TelegramBotService."""

    def setUp(self):
        self.user = User.objects.create_user(
            phone_number="+996555000010",
            password="testpass123",
        )
        self.organization = Organization.objects.create(
            owner=self.user,
            title="Test Org TG Service",
        )
        self.assistant = Assistant.objects.create(
            organization=self.organization,
            name="Test Assistant",
            gender="male",
            position="Consultant",
        )
        self.telegram_bot = TelegramBot.objects.create(
            organization=self.organization,
            bot_token="123456789:ABCdefGHIjklMNOpqrsTUVwxyz",
        )

    @patch("messenger_bots.services.telegram.requests.post")
    def test_get_me_success(self, mock_post):
        """Test successful getMe request."""
        mock_post.return_value.json.return_value = {
            "ok": True,
            "result": {
                "id": 123456789,
                "is_bot": True,
                "first_name": "Test Bot",
                "username": "test_bot",
            },
        }

        service = TelegramBotService(self.telegram_bot)
        result = service.get_me()

        self.assertIsNotNone(result)
        self.assertEqual(result["username"], "test_bot")
        self.telegram_bot.refresh_from_db()
        self.assertEqual(self.telegram_bot.bot_username, "test_bot")

    @patch("messenger_bots.services.telegram.requests.post")
    def test_get_me_failure(self, mock_post):
        """Test failed getMe request."""
        mock_post.return_value.json.return_value = {
            "ok": False,
            "description": "Unauthorized",
        }

        service = TelegramBotService(self.telegram_bot)
        result = service.get_me()

        self.assertIsNone(result)
        self.telegram_bot.refresh_from_db()
        self.assertEqual(self.telegram_bot.last_error, "Unauthorized")

    @patch("messenger_bots.services.telegram.requests.post")
    def test_set_webhook_success(self, mock_post):
        """Test successful webhook setup."""
        mock_post.return_value.json.return_value = {"ok": True}

        service = TelegramBotService(self.telegram_bot)
        result = service.set_webhook("https://example.com/webhook/")

        self.assertTrue(result)
        self.telegram_bot.refresh_from_db()
        self.assertEqual(self.telegram_bot.webhook_url, "https://example.com/webhook/")

    @patch("messenger_bots.services.telegram.requests.post")
    def test_send_message_success(self, mock_post):
        """Test successful message sending."""
        mock_post.return_value.json.return_value = {
            "ok": True,
            "result": {
                "message_id": 123,
                "chat": {"id": 456},
                "text": "Hello!",
            },
        }

        service = TelegramBotService(self.telegram_bot)
        result = service.send_message("456", "Hello!")

        self.assertIsNotNone(result)
        self.assertEqual(result["message_id"], 123)

    @patch("messenger_bots.services.telegram.TelegramBotService.send_message")
    @patch("messenger_bots.services.telegram.TelegramBotService.send_typing_action")
    @patch("messenger_bots.services.assistant.BotAssistantService.get_response")
    def test_process_webhook_update(self, mock_get_response, mock_typing, mock_send):
        """Test processing a Telegram webhook update."""
        mock_get_response.return_value = "AI response"
        mock_send.return_value = {"message_id": 999}

        update = {
            "message": {
                "message_id": 123,
                "chat": {"id": 456},
                "from": {
                    "id": 789,
                    "first_name": "John",
                    "last_name": "Doe",
                    "username": "johndoe",
                },
                "text": "Hello, bot!",
            }
        }

        result = TelegramBotService.process_webhook_update(self.telegram_bot, update)

        self.assertEqual(result, "AI response")

        # Check that chat was created
        chat = BotChat.objects.get(
            organization=self.organization,
            platform=BotPlatform.TELEGRAM,
            platform_chat_id="456",
        )
        self.assertEqual(chat.user_name, "John Doe (@johndoe)")

        # Check that messages were saved
        messages = chat.messages.all()
        self.assertEqual(messages.count(), 2)
        self.assertEqual(messages[0].text, "Hello, bot!")
        self.assertEqual(messages[0].sender, BotMessage.USER)
        self.assertEqual(messages[1].text, "AI response")
        self.assertEqual(messages[1].sender, BotMessage.ASSISTANT)


class WhatsAppBotServiceTest(TestCase):
    """Tests for WhatsAppBotService."""

    def setUp(self):
        self.user = User.objects.create_user(
            phone_number="+996555000011",
            password="testpass123",
        )
        self.organization = Organization.objects.create(
            owner=self.user,
            title="Test Org WA Service",
        )
        self.assistant = Assistant.objects.create(
            organization=self.organization,
            name="Test Assistant WA",
            gender="female",
            position="Sales",
        )
        self.whatsapp_bot = WhatsAppBot.objects.create(
            organization=self.organization,
            phone_number_id="123456789",
            business_account_id="987654321",
            access_token="EAAxxxxxx",
        )

    @patch("messenger_bots.services.whatsapp.requests.get")
    def test_get_phone_number_info_success(self, mock_get):
        """Test successful phone number info request."""
        mock_get.return_value.json.return_value = {
            "display_phone_number": "+1 555 123 4567",
            "verified_name": "Test Business",
        }

        service = WhatsAppBotService(self.whatsapp_bot)
        result = service.get_phone_number_info()

        self.assertIsNotNone(result)
        self.whatsapp_bot.refresh_from_db()
        self.assertEqual(self.whatsapp_bot.display_phone_number, "+1 555 123 4567")

    @patch("messenger_bots.services.whatsapp.requests.post")
    def test_send_message_success(self, mock_post):
        """Test successful message sending."""
        mock_post.return_value.json.return_value = {
            "messaging_product": "whatsapp",
            "contacts": [{"input": "996555123456", "wa_id": "996555123456"}],
            "messages": [{"id": "wamid.xxx"}],
        }

        service = WhatsAppBotService(self.whatsapp_bot)
        result = service.send_message("996555123456", "Hello!")

        self.assertIsNotNone(result)
        self.assertIn("messages", result)

    def test_verify_webhook_signature(self):
        """Test webhook signature verification."""
        import hmac
        import hashlib

        self.whatsapp_bot.webhook_secret = "test_secret"
        self.whatsapp_bot.save()

        payload = b'{"test": "data"}'
        expected_sig = hmac.new(
            b"test_secret", payload, hashlib.sha256
        ).hexdigest()

        result = WhatsAppBotService.verify_webhook_signature(
            self.whatsapp_bot,
            payload,
            f"sha256={expected_sig}",
        )
        self.assertTrue(result)

        # Test with wrong signature
        result = WhatsAppBotService.verify_webhook_signature(
            self.whatsapp_bot,
            payload,
            "sha256=wrong_signature",
        )
        self.assertFalse(result)

    @patch("messenger_bots.services.whatsapp.WhatsAppBotService.send_message")
    @patch("messenger_bots.services.whatsapp.WhatsAppBotService.mark_as_read")
    @patch("messenger_bots.services.assistant.BotAssistantService.get_response")
    def test_process_webhook_update(self, mock_get_response, mock_read, mock_send):
        """Test processing a WhatsApp webhook update."""
        mock_get_response.return_value = "AI response"
        mock_send.return_value = {"messages": [{"id": "wamid.xxx"}]}

        data = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "id": "wamid.123",
                            "from": "996555123456",
                            "type": "text",
                            "text": {"body": "Hello!"},
                        }],
                        "contacts": [{
                            "profile": {"name": "John Doe"},
                        }],
                    }
                }]
            }]
        }

        result = WhatsAppBotService.process_webhook_update(self.whatsapp_bot, data)

        self.assertEqual(result, "AI response")

        # Check that chat was created
        chat = BotChat.objects.get(
            organization=self.organization,
            platform=BotPlatform.WHATSAPP,
            platform_chat_id="996555123456",
        )
        self.assertEqual(chat.user_name, "John Doe")
        self.assertEqual(chat.user_phone, "996555123456")

        # Check that messages were saved
        messages = chat.messages.all()
        self.assertEqual(messages.count(), 2)
