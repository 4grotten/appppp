from .base import *

# run synchronously
CELERY_TASK_ALWAYS_EAGER = True

# Raise exceptions in celery tasks
CELERY_TASK_EAGER_PROPAGATES = True

CELERY_BROKER_URL = 'amqp://localhost:5672'
