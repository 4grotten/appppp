from django.contrib import admin

from api_keys.models import GeminiConfig, GPTAssistConfig, InstagramConfig, ChatGPTConfig, GeminiTextModelConfig, GeminiImageModelConfig, AWSConfig
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


@admin.register(GeminiTextModelConfig)
class GeminiTextModelConfigAdmin(admin.ModelAdmin):
    list_display = ('id', 'model_name', 'is_active', 'created_at', 'updated_at')
    list_editable = ('is_active',)
    list_filter = ('is_active', 'created_at')
    search_fields = ('model_name',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ("Model", {
            "fields": ("model_name",),
            "description": "Enter text model name (without 'models/' prefix), e.g. gemini-2.5-pro"
        }),
        ("Status", {
            "fields": ("is_active",)
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )


@admin.register(GeminiImageModelConfig)
class GeminiImageModelConfigAdmin(admin.ModelAdmin):
    list_display = ('id', 'model_name', 'is_active', 'created_at', 'updated_at')
    list_editable = ('is_active',)
    list_filter = ('is_active', 'created_at')
    search_fields = ('model_name',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ("Model", {
            "fields": ("model_name",),
            "description": "Enter image model name (without 'models/' prefix), e.g. gemini-3-pro-image-preview"
        }),
        ("Status", {
            "fields": ("is_active",)
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )


@admin.register(GeminiConfig)
class GeminiConfigAdmin(admin.ModelAdmin):
    list_display = ('api_key_masked', 'is_active', 'text_model_info', 'image_model_info', 'created_at', 'updated_at')
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

    def text_model_info(self, obj):
        if obj.model_for_text:
            return obj.model_for_text.model_name
        return "-"
    text_model_info.short_description = "Text Model"

    def image_model_info(self, obj):
        if obj.model_for_image:
            return obj.model_for_image.model_name
        return "-"
    image_model_info.short_description = "Image Model"

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


@admin.register(AWSConfig)
class AWSConfigAdmin(admin.ModelAdmin):
    list_display = ("id", "is_active", "created_at", "updated_at")
    list_filter = ("is_active", "created_at")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("AWS Credentials", {
            "fields": ("access_key_id", "secret_access_key", "is_active"),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )