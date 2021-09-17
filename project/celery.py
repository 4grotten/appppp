import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings.base')

app = Celery('project')
app.config_from_object('django.conf:settings', namespace='CELERY')
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
    'update-login-device-data': {
        'task': 'organizations.tasks.update_login_device_settings',
        'schedule': crontab(hour=1, minute=0)
    },
    'delete-expired-video': {
        'task': 'organizations.tasks.delete_expired_video_url',
        'schedule': crontab(hour='*/1', minute=0)
        # 'schedule': crontab(minute='*/5')
    },
    'delete-expired-photo-and-posts': {
        'task': 'organizations.tasks.delete_expired_photo_and_posts',
        'schedule': crontab(hour='*/1', minute=2)
    },
}
