import atexit
import os

from django.apps import AppConfig


def _graceful_shutdown():
    """Close HTTP sessions on application shutdown.

    This ensures proper cleanup of connection pools to avoid
    resource leaks and connection warnings on shutdown.
    """
    try:
        from messenger_bots.services.whatsapp.http_client import close_waha_session
        close_waha_session()
    except Exception:
        pass

    try:
        from messenger_bots.services.telegram_http_client import close_telegram_session
        close_telegram_session()
    except Exception:
        pass


class MessengerBotsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "messenger_bots"
    verbose_name = "Messenger Bots"

    def ready(self):
        """Run cache warmup task on server startup and register signals."""
        # Import signals to register them
        import messenger_bots.signals  # noqa: F401

        # Register graceful shutdown hook
        atexit.register(_graceful_shutdown)

        # Only run in main process (not in migrations, shell, etc.)
        # Check for RUN_MAIN to avoid double execution in dev server
        is_main_process = os.environ.get("RUN_MAIN") == "true"
        is_gunicorn = "gunicorn" in os.environ.get("SERVER_SOFTWARE", "")
        is_celery = "celery" in os.environ.get("_", "")

        # Skip in celery workers and migrations
        if is_celery:
            return

        # Run in gunicorn or Django dev server main process
        if is_main_process or is_gunicorn:
            try:
                from messenger_bots.tasks import cache_assistant_training_data
                # Delay 5 seconds to let server fully start
                cache_assistant_training_data.apply_async(countdown=5)
                print("[STARTUP] Scheduled cache warmup task (5s delay)")
            except Exception as e:
                print(f"[STARTUP] Failed to schedule cache warmup: {e}")
