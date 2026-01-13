import json
from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch, MagicMock
from rest_framework.test import APIClient

from messenger_bots.models import TelegramBot, WhatsAppBot, BotChat, BotPlatform
from organizations.models import Organization, Assistant
from users.models import User, MyOwnToken


class TelegramWebhookViewTest(TestCase):
    """Tests for Telegram webhook endpoint."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            phone_number="+996555000020",
            password="testpass123",
        )
        self.organization = Organization.objects.create(
            owner=self.user,
            title="Test Org Webhook",
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
            webhook_secret="test_secret_123",
        )

    def test_webhook_without_secret_returns_403(self):
        """Test that webhook without secret token returns 403."""
        response = self.client.post(
            f"/api/v1/messenger-bots/telegram/webhook/{self.organization.id}/",
            data=json.dumps({"message": {"text": "test"}}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)

    def test_webhook_with_wrong_secret_returns_403(self):
        """Test that webhook with wrong secret returns 403."""
        response = self.client.post(
            f"/api/v1/messenger-bots/telegram/webhook/{self.organization.id}/",
            data=json.dumps({"message": {"text": "test"}}),
            content_type="application/json",
            HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN="wrong_secret",
        )
        self.assertEqual(response.status_code, 403)

    @patch("messenger_bots.services.telegram.TelegramBotService.process_webhook_update")
    def test_webhook_with_correct_secret_returns_200(self, mock_process):
        """Test that webhook with correct secret returns 200."""
        response = self.client.post(
            f"/api/v1/messenger-bots/telegram/webhook/{self.organization.id}/",
            data=json.dumps({
                "message": {
                    "message_id": 1,
                    "chat": {"id": 123},
                    "from": {"id": 456, "first_name": "Test"},
                    "text": "Hello",
                }
            }),
            content_type="application/json",
            HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN="test_secret_123",
        )
        self.assertEqual(response.status_code, 200)
        mock_process.assert_called_once()

    def test_webhook_for_nonexistent_org_returns_404(self):
        """Test that webhook for non-existent org returns 404."""
        response = self.client.post(
            "/api/v1/messenger-bots/telegram/webhook/99999/",
            data=json.dumps({"message": {"text": "test"}}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)


class WhatsAppWebhookViewTest(TestCase):
    """Tests for WhatsApp webhook endpoint."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            phone_number="+996555000021",
            password="testpass123",
        )
        self.organization = Organization.objects.create(
            owner=self.user,
            title="Test Org WA Webhook",
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
            verify_token="my_verify_token",
        )

    def test_webhook_verification_success(self):
        """Test successful webhook verification (GET request)."""
        response = self.client.get(
            f"/api/v1/messenger-bots/whatsapp/webhook/{self.organization.id}/",
            {
                "hub.mode": "subscribe",
                "hub.verify_token": "my_verify_token",
                "hub.challenge": "test_challenge_123",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "test_challenge_123")

    def test_webhook_verification_wrong_token(self):
        """Test webhook verification with wrong token."""
        response = self.client.get(
            f"/api/v1/messenger-bots/whatsapp/webhook/{self.organization.id}/",
            {
                "hub.mode": "subscribe",
                "hub.verify_token": "wrong_token",
                "hub.challenge": "test_challenge_123",
            },
        )
        self.assertEqual(response.status_code, 403)

    @patch("messenger_bots.services.whatsapp.WhatsAppBotService.process_webhook_update")
    def test_webhook_message_processing(self, mock_process):
        """Test message processing (POST request)."""
        response = self.client.post(
            f"/api/v1/messenger-bots/whatsapp/webhook/{self.organization.id}/",
            data=json.dumps({
                "entry": [{
                    "changes": [{
                        "value": {
                            "messages": [{
                                "id": "wamid.123",
                                "from": "996555123456",
                                "type": "text",
                                "text": {"body": "Hello!"},
                            }]
                        }
                    }]
                }]
            }),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        mock_process.assert_called_once()


class TelegramBotAPIViewTest(TestCase):
    """Tests for Telegram bot management API."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            phone_number="+996555000022",
            password="testpass123",
        )
        self.organization = Organization.objects.create(
            owner=self.user,
            title="Test Org API",
        )
        self.assistant = Assistant.objects.create(
            organization=self.organization,
            name="Test Assistant API",
            gender="male",
            position="Manager",
        )
        self.token = MyOwnToken.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def test_get_telegram_bot_not_configured(self):
        """Test getting non-existent Telegram bot config."""
        response = self.client.get(
            f"/api/v1/messenger-bots/telegram/{self.organization.id}/"
        )
        self.assertEqual(response.status_code, 404)

    @patch("messenger_bots.services.telegram.TelegramBotService.setup_bot")
    def test_create_telegram_bot(self, mock_setup):
        """Test creating Telegram bot configuration."""
        mock_setup.return_value = True

        response = self.client.post(
            f"/api/v1/messenger-bots/telegram/{self.organization.id}/",
            {"bot_token": "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"},
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(TelegramBot.objects.filter(organization=self.organization).exists())

    def test_create_telegram_bot_invalid_token(self):
        """Test creating Telegram bot with invalid token."""
        response = self.client.post(
            f"/api/v1/messenger-bots/telegram/{self.organization.id}/",
            {"bot_token": "invalid_token_without_colon"},
        )
        self.assertEqual(response.status_code, 400)

    def test_create_telegram_bot_without_assistant(self):
        """Test creating Telegram bot when organization has no assistant."""
        self.assistant.delete()
        response = self.client.post(
            f"/api/v1/messenger-bots/telegram/{self.organization.id}/",
            {"bot_token": "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("assistant", response.json()["error"].lower())

    def test_access_denied_for_non_owner(self):
        """Test that non-owner cannot access bot configuration."""
        other_user = User.objects.create_user(
            phone_number="+996555000099",
            password="testpass123",
        )
        other_token = MyOwnToken.objects.create(user=other_user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {other_token.key}")

        response = self.client.get(
            f"/api/v1/messenger-bots/telegram/{self.organization.id}/"
        )
        self.assertEqual(response.status_code, 404)


class BotStatusAPIViewTest(TestCase):
    """Tests for bot status API."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            phone_number="+996555000023",
            password="testpass123",
        )
        self.organization = Organization.objects.create(
            owner=self.user,
            title="Test Org Status",
        )
        self.token = MyOwnToken.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def test_status_no_bots_no_assistant(self):
        """Test status when no bots or assistant configured."""
        response = self.client.get(
            f"/api/v1/messenger-bots/status/{self.organization.id}/"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["has_assistant"])
        self.assertFalse(data["telegram"]["configured"])
        self.assertFalse(data["whatsapp"]["configured"])

    def test_status_with_assistant_and_telegram(self):
        """Test status with assistant and Telegram bot."""
        Assistant.objects.create(
            organization=self.organization,
            name="Test",
            gender="male",
            position="Test",
        )
        TelegramBot.objects.create(
            organization=self.organization,
            bot_token="123:abc",
            bot_username="test_bot",
        )

        response = self.client.get(
            f"/api/v1/messenger-bots/status/{self.organization.id}/"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["has_assistant"])
        self.assertTrue(data["telegram"]["configured"])
        self.assertEqual(data["telegram"]["username"], "test_bot")
        self.assertFalse(data["whatsapp"]["configured"])
