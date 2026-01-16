import os

from django.apps import AppConfig


class MessengerBotsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "messenger_bots"
    verbose_name = "Messenger Bots"

    def ready(self):
        """Run cache warmup task on server startup."""
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
