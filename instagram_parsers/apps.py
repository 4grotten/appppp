from django.apps import AppConfig


class InstagramParsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'instagram_parsers'

    def ready(self):
        import instagram_parsers.signals