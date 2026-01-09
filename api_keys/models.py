import logging
import os
import threading

import requests
from django.db import models

from common.models import ChatGPTSettings, TimestampModel

# Create your models here.
from instagram_parsers.models import InstagramApi


class InstagramConfig(InstagramApi):
    class Meta:
        proxy = True
        app_label = 'api_keys'
        verbose_name = "Instagram Api"
        verbose_name_plural = "Instagram Api"

class ChatGPTConfig(ChatGPTSettings):
    class Meta:
        proxy = True
        app_label = 'api_keys'
        verbose_name = "ChatGpt Description Api"
        verbose_name_plural = "ChatGpt Description Api"


class GeminiConfig(TimestampModel):
    api_key = models.CharField(
        max_length=255,
        verbose_name="Gemini API Key",
        help_text="Start with AIza...", null=True, blank=True
    )
    is_active = models.BooleanField(default=False, null=True, blank=True)

    class Meta:
        verbose_name = "Gemini Api"
        verbose_name_plural = "Gemini Api"

    def __str__(self):
        return f"Gemini Config ({'Active' if self.is_active else 'Disabled'})"

    def save(self, *args, **kwargs):
        old = None
        if self.pk:
            try:
                old = GeminiConfig.objects.get(pk=self.pk)
            except GeminiConfig.DoesNotExist:
                old = None

        if self.is_active:
            GeminiConfig.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)

        super().save(*args, **kwargs)

        key_changed = False
        if old is None and self.api_key:
            key_changed = True
        elif old and (old.api_key != (self.api_key or "")):
            key_changed = True

        if key_changed and self.is_active and self.api_key:
            logger = logging.getLogger(__name__)

            def _send():
                webhook = os.environ.get(
                    "GEMINI_SERVICE_WEBHOOK_URL",
                    "http://gemini-api:8002/internal/update_api_key",
                )
                try:
                    logger.info("Sending updated Gemini API key to %s", webhook)
                    resp = requests.post(webhook, json={"api_key": self.api_key}, timeout=5)
                    if resp.ok:
                        logger.info("Successfully updated Gemini API key (status %s)", resp.status_code)
                    else:
                        logger.warning(
                            "Failed to update Gemini API key: status=%s body=%s",
                            resp.status_code,
                            resp.text,
                        )
                except Exception as e:
                    logger.exception("Error sending Gemini API key to %s: %s", webhook, e)

            threading.Thread(target=_send, daemon=True).start()



class GPTAssistConfig(TimestampModel):
    api_key = models.CharField(
        max_length=255,
        verbose_name="Gpt assistant API Key",
        help_text="Start with AIza...", null=True, blank=True
    )
    is_active = models.BooleanField(default=False, null=True, blank=True)

    class Meta:
        verbose_name = "GPT assistant  Api"
        verbose_name_plural = "GPT assistant  Api"

    def __str__(self):
        return f"GPT assistant Config ({'Active' if self.is_active else 'Disabled'})"

    def save(self, *args, **kwargs):
        if self.is_active:
            GPTAssistConfig.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)

        super().save(*args, **kwargs)
