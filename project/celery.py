import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings.base")

app = Celery("project")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    # 'delete-old-insta-posts': {
    #     'task': 'organizations.tasks.delete_old_instagram_posts',
    #     'schedule': crontab(hour=0, minute=5)
    # },
    # 'update-one-insta-video-every-30-seconds': {
    #     'task': 'organizations.tasks.update_instagram_videos',
    #     'schedule': 30
    # },
    "update-login-device-data": {
        "task": "organizations.tasks.update_login_device_settings",
        # 'schedule': crontab(hour=1, minute=0)
        "schedule": crontab(0, 0, day_of_month="1"),
    },
    "delete-expired-video": {
        "task": "organizations.tasks.delete_expired_video_url",
        "schedule": crontab(hour="*/1", minute=0),
        # 'schedule': crontab(minute='*/5')
    },
    "delete-expired-photo-and-posts": {
        "task": "organizations.tasks.delete_expired_photo_and_posts",
        "schedule": crontab(hour="*/1", minute=2),
    },
    "update-posts-daily": {
        "task": "organizations.tasks.update_posts",
        "schedule": crontab(minute=0, hour=0),
    },
    "delete-expired-coupons": {
        "task": "organizations.tasks.expire_coupons",
        "schedule": crontab(minute=0, hour=0),
    },
    # Messenger Bots Tasks
    "reset-userbot-daily-counters": {
        "task": "messenger_bots.tasks.reset_userbot_daily_counters",
        "schedule": crontab(minute=0, hour=0),  # Every day at midnight
    },
    "check-pending-bot-requests": {
        "task": "messenger_bots.tasks.check_pending_bot_requests",
        "schedule": crontab(minute="*/5"),  # Every 5 minutes
    },
    "check-waha-session-health": {
        "task": "messenger_bots.tasks.check_waha_session_health",
        "schedule": crontab(minute="*/10"),  # Every 10 minutes
    },
    "sync-waha-session-status": {
        "task": "messenger_bots.tasks.sync_waha_session_status",
        "schedule": crontab(minute="*/15"),  # Every 15 minutes
    },
    # AI Assistant cache task - pre-warm cache for fast responses
    "cache-assistant-training-data": {
        "task": "messenger_bots.tasks.cache_assistant_training_data",
        "schedule": crontab(minute="*/20"),  # Every 20 minutes
    },
}
