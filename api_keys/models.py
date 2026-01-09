from django.db import models

# Create your models here.
from instagram_parsers.models import InstagramApi
from common.models import ChatGPTSettings, TimestampModel


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
        if self.is_active:
            GeminiConfig.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)

        super().save(*args, **kwargs)



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