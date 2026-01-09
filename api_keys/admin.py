from django.contrib import admin

from api_keys.models import GeminiConfig, GPTAssistConfig, InstagramConfig, ChatGPTConfig
from instagram_parsers.models import InstagramApi
from common.models import ChatGPTSettings
# Register your models here.


@admin.register(ChatGPTConfig)
class ChatGPTSettingsAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "is_active",
        "model",
        "temperature",
        "max_tokens",
        "api_key_masked",
        "updated_at",
    ]
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = (
        (None, {
            "fields": ("is_active",)
        }),
        ("API Configuration", {
            "fields": ("api_key", "model", "temperature"),
            "description": "Настройки подключения к OpenAI ChatGPT API"
        }),
        ("Generation Parameters", {
            "fields": ("max_tokens", ("min_sentences", "max_sentences"), ("min_words", "max_words")),
            "description": "Параметры генерации текста: длина ответа и количество предложений/слов"
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    def api_key_masked(self, obj):
        """Показывает замаскированный API ключ для безопасности."""
        if obj.api_key:
            return f"{obj.api_key[:10]}...{obj.api_key[-4:]}"
        return "Not set"
    api_key_masked.short_description = "API Key"

    def has_add_permission(self, request):
        # Разрешаем добавление только если нет записей
        return not ChatGPTSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Запрещаем удаление singleton
        return False


@admin.register(InstagramConfig)
class InstagramApiAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'password', 'api_key', 'proxy', 'is_active','created_at', 'updated_at',)

    # def save_model(self, request, obj, form, change):
    #     if not obj.api_key:
    #         proxy = f'http://{obj.proxy.login}:{obj.proxy.password}@{obj.proxy.http_s}'
    #         obj.api_key = parser.get_api_key(obj.username, obj.password, proxy=proxy)
    #         obj.is_active = True
    #     super().save_model(request, obj, form, change)


@admin.register(GeminiConfig)
class GeminiConfigAdmin(admin.ModelAdmin):
    list_display = ('api_key','is_active', 'created_at', 'updated_at')


@admin.register(GPTAssistConfig)
class GPTAssistConfigAdmin(admin.ModelAdmin):
    list_display = ('api_key', 'is_active', 'created_at', 'updated_at')