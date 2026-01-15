from django.test import TestCase
from django.db import IntegrityError
from unittest.mock import patch, MagicMock

from messenger_bots.models import (
    TelegramBot,
    WhatsAppBot,
    BotChat,
    BotMessage,
    BotPlatform,
)
from organizations.models import Organization, Assistant
from users.models import User


class TelegramBotModelTest(TestCase):
    """Tests for TelegramBot model."""

    def setUp(self):
        self.user = User.objects.create_user(
            phone_number="+996555000001",
            password="testpass123",
        )
        self.organization = Organization.objects.create(
            owner=self.user,
            title="Test Organization",
        )

    def test_create_telegram_bot(self):
        """Test creating a Telegram bot."""
        bot = TelegramBot.objects.create(
            organization=self.organization,
            bot_token="123456789:ABCdefGHIjklMNOpqrsTUVwxyz",
        )
        self.assertIsNotNone(bot.webhook_secret)
        self.assertEqual(len(bot.webhook_secret), 64)  # hex(32) = 64 chars
        self.assertTrue(bot.is_active)

    def test_telegram_bot_unique_per_organization(self):
        """Test that only one Telegram bot per organization is allowed."""
        TelegramBot.objects.create(
            organization=self.organization,
            bot_token="123456789:ABCdefGHIjklMNOpqrsTUVwxyz",
        )
        with self.assertRaises(IntegrityError):
            TelegramBot.objects.create(
                organization=self.organization,
                bot_token="987654321:ZYXwvuTSRqponMLKjihGFEdcba",
            )

    def test_webhook_secret_auto_generated(self):
        """Test that webhook secret is auto-generated if not provided."""
        bot = TelegramBot(
            organization=self.organization,
            bot_token="123456789:ABCdefGHIjklMNOpqrsTUVwxyz",
        )
        self.assertIsNone(bot.webhook_secret)
        bot.save()
        self.assertIsNotNone(bot.webhook_secret)


class WhatsAppBotModelTest(TestCase):
    """Tests for WhatsAppBot model."""

    def setUp(self):
        self.user = User.objects.create_user(
            phone_number="+996555000002",
            password="testpass123",
        )
        self.organization = Organization.objects.create(
            owner=self.user,
            title="Test Organization WA",
        )

    def test_create_whatsapp_bot(self):
        """Test creating a WhatsApp bot."""
        bot = WhatsAppBot.objects.create(
            organization=self.organization,
            phone_number_id="123456789",
            business_account_id="987654321",
            access_token="EAAxxxxxx",
        )
        self.assertIsNotNone(bot.verify_token)
        self.assertTrue(bot.is_active)

    def test_verify_token_auto_generated(self):
        """Test that verify token is auto-generated if not provided."""
        bot = WhatsAppBot(
            organization=self.organization,
            phone_number_id="123456789",
            business_account_id="987654321",
            access_token="EAAxxxxxx",
        )
        self.assertIsNone(bot.verify_token)
        bot.save()
        self.assertIsNotNone(bot.verify_token)


class BotChatModelTest(TestCase):
    """Tests for BotChat model."""

    def setUp(self):
        self.user = User.objects.create_user(
            phone_number="+996555000003",
            password="testpass123",
        )
        self.organization = Organization.objects.create(
            owner=self.user,
            title="Test Organization Chat",
        )

    def test_create_telegram_chat(self):
        """Test creating a Telegram chat."""
        chat = BotChat.objects.create(
            organization=self.organization,
            platform=BotPlatform.TELEGRAM,
            platform_chat_id="123456789",
            user_name="Test User",
        )
        self.assertEqual(chat.platform, BotPlatform.TELEGRAM)
        self.assertTrue(chat.is_active)

    def test_create_whatsapp_chat(self):
        """Test creating a WhatsApp chat."""
        chat = BotChat.objects.create(
            organization=self.organization,
            platform=BotPlatform.WHATSAPP,
            platform_chat_id="996555123456",
            user_name="Test User",
            user_phone="996555123456",
        )
        self.assertEqual(chat.platform, BotPlatform.WHATSAPP)

    def test_unique_chat_constraint(self):
        """Test that chat is unique per organization, platform, and chat_id."""
        BotChat.objects.create(
            organization=self.organization,
            platform=BotPlatform.TELEGRAM,
            platform_chat_id="123456789",
        )
        with self.assertRaises(IntegrityError):
            BotChat.objects.create(
                organization=self.organization,
                platform=BotPlatform.TELEGRAM,
                platform_chat_id="123456789",
            )


class BotMessageModelTest(TestCase):
    """Tests for BotMessage model."""

    def setUp(self):
        self.user = User.objects.create_user(
            phone_number="+996555000004",
            password="testpass123",
        )
        self.organization = Organization.objects.create(
            owner=self.user,
            title="Test Organization Msg",
        )
        self.chat = BotChat.objects.create(
            organization=self.organization,
            platform=BotPlatform.TELEGRAM,
            platform_chat_id="123456789",
        )

    def test_create_user_message(self):
        """Test creating a user message."""
        message = BotMessage.objects.create(
            chat=self.chat,
            sender=BotMessage.USER,
            text="Hello, bot!",
        )
        self.assertEqual(message.sender, BotMessage.USER)

    def test_create_assistant_message(self):
        """Test creating an assistant message."""
        message = BotMessage.objects.create(
            chat=self.chat,
            sender=BotMessage.ASSISTANT,
            text="Hello! How can I help you?",
        )
        self.assertEqual(message.sender, BotMessage.ASSISTANT)

    def test_messages_ordered_by_created_at(self):
        """Test that messages are ordered by creation time."""
        msg1 = BotMessage.objects.create(
            chat=self.chat,
            sender=BotMessage.USER,
            text="First message",
        )
        msg2 = BotMessage.objects.create(
            chat=self.chat,
            sender=BotMessage.ASSISTANT,
            text="Second message",
        )
        messages = list(self.chat.messages.all())
        self.assertEqual(messages[0], msg1)
        self.assertEqual(messages[1], msg2)
