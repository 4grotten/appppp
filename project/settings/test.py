from .base import *

# run synchronously
CELERY_TASK_ALWAYS_EAGER = True

# Raise exceptions in celery tasks
CELERY_TASK_EAGER_PROPAGATES = True

CELERY_BROKER_URL = 'amqp://localhost:5672'

DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

TEST_RUNNER = 'xmlrunner.extra.djangotestrunner.XMLTestRunner'

TEST_OUTPUT_FILE_NAME = 'junittestreport.xml'
