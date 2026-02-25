from django.contrib import admin

from api_keys.models import GeminiConfig, GPTAssistConfig, InstagramConfig, ChatGPTConfig, GeminiModelConfig
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
        ("Account Login", {
            "fields": ("link","login","password"),
            "description": "Данные аккаунта"
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
    list_display = ('id', 'username',  'api_key', 'proxy', 'is_active','created_at', 'updated_at',)
    fieldsets = (
        ("API Key", {
            "fields": ("api_key", 'is_active'),
            "description": "API Key for Instagram"
        }),
    ("Account Login", {
        "fields": ("link", "login", "password"),
        "description": "Данные аккаунта"
    }),
    )

    # def save_model(self, request, obj, form, change):
    #     if not obj.api_key:
    #         proxy = f'http://{obj.proxy.login}:{obj.proxy.password}@{obj.proxy.http_s}'
    #         obj.api_key = parser.get_api_key(obj.username, obj.password, proxy=proxy)
    #         obj.is_active = True
    #     super().save_model(request, obj, form, change)


@admin.register(GeminiModelConfig)
class GeminiModelConfigAdmin(admin.ModelAdmin):
    list_display = ('id',  'text_model', 'image_model', 'is_active', 'created_at', 'updated_at')
    list_editable = ('is_active',)
    list_filter = ('is_active', 'created_at')
    search_fields = ('text_model', 'image_model')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ("Models", {
            "fields": ("text_model", "image_model"),
            "description": "Configure which model names to use for text and image generation"
        }),
        ("Status", {
            "fields": ("is_active",)
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    def save_model(self, request, obj, form, change):
        if obj.is_active:
            GeminiModelConfig.objects.filter(is_active=True).exclude(pk=obj.pk).update(is_active=False)
        super().save_model(request, obj, form, change)


@admin.register(GeminiConfig)
class GeminiConfigAdmin(admin.ModelAdmin):
    list_display = ('api_key_masked', 'is_active', 'model_for_text', 'model_for_image', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
    list_filter = ('is_active', 'created_at')

    fieldsets = (
        ("API Key", {
            "fields": ("api_key", 'is_active'),
            "description": "API Key for Gemini"
        }),
        ("Models", {
            "fields": ("model_for_text", "model_for_image"),
            "description": "Select which model configurations to use"
        }),
        ("Account Login", {
            "fields": ("link", "login", "password"),
            "description": "Данные аккаунта (опционально)"
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

    def save_model(self, request, obj, form, change):
        if obj.is_active:
            GeminiConfig.objects.filter(is_active=True).exclude(pk=obj.pk).update(is_active=False)
        super().save_model(request, obj, form, change)


@admin.register(GPTAssistConfig)
class GPTAssistConfigAdmin(admin.ModelAdmin):
    list_display = ('api_key', 'is_active', 'created_at', 'updated_at')
    fieldsets = (
        ("API Key", {
            "fields": ("api_key",'is_active'),
            "description": "API Key for Gemini"
        }),
        ("Account Login", {
            "fields": ("link", "login", "password"),
            "description": "Данные аккаунта"
        }),
    )