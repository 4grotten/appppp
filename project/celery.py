import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings.base')

app = Celery('project')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'add-every-day': {
        'task': 'shop.tasks.update_instagram_videos',
        'schedule': crontab(hour=0, minute=0)
    },
}
