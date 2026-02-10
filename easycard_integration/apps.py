"""EasyCard Integration app configuration."""

from django.apps import AppConfig


class EasycardIntegrationConfig(AppConfig):
    """Configuration for EasyCard Integration app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "easycard_integration"
    verbose_name = "EasyCard Integration"

    def ready(self):
        """Import signals when app is ready."""
        pass
