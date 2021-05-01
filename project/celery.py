import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings.base')

app = Celery('project')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'delete-old-insta-posts': {
        'task': 'shop.tasks.delete_old_instagram_posts',
        'schedule': crontab(hour=0, minute=5)
    },
    'update-one-insta-video-every-30-seconds': {
        'task': 'shop.tasks.update_instagram_videos',
        'schedule': 30
    },
}
