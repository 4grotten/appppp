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


class GeminiModelConfig(TimestampModel):
    text_model = models.CharField(max_length=100, verbose_name="Text Model Name", help_text="Model name to use for text generation, e.g. gemini-2.5-pro")
    image_model = models.CharField(max_length=100, verbose_name="Image Model Name", help_text="Model name to use for image generation, e.g. gemini-3-pro-image-preview")
    is_active = models.BooleanField(default=False, verbose_name="Is Active", help_text="Whether this model is active and should be used for generation")

    class Meta:
        verbose_name = "Gemini Model Config"
        verbose_name_plural = "Gemini Model Configs"
        ordering = ['-created_at']

    def __str__(self):
        return f"Text: {self.text_model} | Image: {self.image_model} ({'Active' if self.is_active else 'Inactive'})"
    
class GeminiConfig(TimestampModel):
    api_key = models.CharField(
        max_length=255,
        verbose_name="Gemini API Key",
        help_text="Start with AIza...", null=True, blank=True
    )
    is_active = models.BooleanField(default=False, null=True, blank=True)
    link = models.CharField(max_length=255, null=True, blank=True)
    login = models.CharField(max_length=255, null=True, blank=True)
    password = models.CharField(max_length=255, null=True, blank=True)
    model_for_text = models.ForeignKey(GeminiModelConfig, on_delete=models.SET_NULL, null=True, blank=True, related_name="gemini_configs_text", verbose_name="Gemini Model", help_text="Model to use for text generation")
    model_for_image = models.ForeignKey(GeminiModelConfig, on_delete=models.SET_NULL, null=True, blank=True, related_name="gemini_configs_image", verbose_name="Gemini Image Model", help_text="Model to use for image generation")

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
    link = models.CharField(max_length=255, null=True, blank=True)
    login = models.CharField(max_length=255, null=True, blank=True)
    password = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        verbose_name = "GPT assistant  Api"
        verbose_name_plural = "GPT assistant  Api"

    def __str__(self):
        return f"GPT assistant Config ({'Active' if self.is_active else 'Disabled'})"

    def save(self, *args, **kwargs):
        if self.is_active:
            GPTAssistConfig.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)

        super().save(*args, **kwargs)
