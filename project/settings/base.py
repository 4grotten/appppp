import json
import os
from distutils.util import strtobool

from corsheaders.defaults import default_headers
from decouple import config
from django.utils.translation import gettext_lazy as _
from kombu.serialization import registry

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = strtobool(config('DEBUG', default='false'))

ALLOWED_HOSTS = config('ALLOWED_HOSTS').split(',')

# Application definition

INSTALLED_APPS = [
    'modeltranslation',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',

    'common.apps.CoreConfig',
    'transactions.apps.TransactionsConfig',
    'organizations.apps.OrganizationsConfig',
    'users.apps.UsersConfig',
    'notifications',
    'shop.apps.ShopConfig',

    'rest_framework',
    'rest_framework.authtoken',
    'rest_auth',
    'corsheaders',
    'mapwidgets',
    'imagekit',
    'fcm_django',
    'drf_multiple_model',
    'storages',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'common.exception_handler_middleware.RequestExceptionHandlerMiddleware',
]

ROOT_URLCONF = 'project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
            os.path.join(BASE_DIR, 'frontend')
        ]
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'project.wsgi.application'

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': config('POSTGRES_DB'),
        'PASSWORD': config('POSTGRES_PASSWORD'),
        'USER': config('POSTGRES_USER'),
        'HOST': config('POSTGRES_HOST'),
        'PORT': config('POSTGRES_PORT'),
        'OPTIONS': json.loads(config('POSTGRES_OPTIONS', default="{}")),
    }
}

# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LOCALE_PATHS = ['locale', ]

LANGUAGE_CODE = 'en-us'

LANGUAGES = (
    ('ru', _('Russian')),
    ('en', _('English')),
    ('tr', _('Turkish')),
)

MODELTRANSLATION_DEFAULT_LANGUAGE = 'ru'
MODELTRANSLATION_LANGUAGES = ('ru', 'en', 'tr',)
MODELTRANSLATION_AVAILABLE_LANGUAGES = ('ru', 'en', 'tr',)
MODELTRANSLATION_FALLBACK_LANGUAGES = ('ru', 'en', 'tr',)

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'frontend'),  # update the STATICFILES_DIRS
)

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

# AWS settings

AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME', default='eu-central-1')
AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME')
AWS_DEFAULT_ACL = 'public-read'
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400'}
AWS_S3_FILE_OVERWRITE = False

DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

IMAGEKIT_DEFAULT_CACHEFILE_BACKEND = 'imagekit.cachefiles.backends.Async'
IMAGEKIT_DEFAULT_CACHEFILE_STRATEGY = 'imagekit.cachefiles.strategies.Optimistic'

CELERY_ACCEPT_CONTENT = ['json', 'application/text', 'pickle']

AUTH_USER_MODEL = 'users.User'

# CORS Configurations

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = False

CORS_ALLOW_METHODS = (
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
)

CORS_ALLOW_HEADERS = list(default_headers) + [
    'Currency',
]

SESSION_COOKIE_SAMESITE = None

CORS_PREFLIGHT_MAX_AGE = 86400

# REST FRAMEWORK
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_FILTER_BACKENDS': ('django_filters.rest_framework.DjangoFilterBackend',),
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.NamespaceVersioning',
    'DEFAULT_PAGINATION_CLASS': 'common.pagination.GeneralPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'common.schemas.DefaultSchema',
    'COERCE_DECIMAL_TO_STRING': False,
}

NIKITA_URL = 'https://smspro.nikita.kg/api/message'
NIKITA_USERNAME = config('NIKITA_USERNAME')
NIKITA_PASSWORD = config('NIKITA_PASSWORD')
NIKITA_SENDER = config('NIKITA_SENDER')
NIKITA_TEST_MODE = int(config('NIKITA_TEST_MODE', default=1))

OER_APP_ID = config('OER_APP_ID')
OER_CACHE_TIMEOUT = 60 * 60 * 5
OER_BASE_CURRENCY = 'USD'

APP_BASE_CURRENCY = 'KGS'

EMAIL_HOST = 'smtp.yandex.ru'
EMAIL_PORT = 587
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='login@yandex.ru')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='password')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='from@yandex.ru')
EMAIL_USE_TLS = True

FCM_DJANGO_SETTINGS = {
    "APP_VERBOSE_NAME": 'Qrcode push',
    # default: _('FCM Django')
    "FCM_SERVER_KEY": config('FCM_KEY'),
    # true if you want to have only one active device per registered user at a time
    # default: False
    "ONE_DEVICE_PER_USER": False,
    # devices to which notifications cannot be sent,
    # are deleted upon receiving error response from FCM
    # default: False
    "DELETE_INACTIVE_DEVICES": False,
}

HOST_URL = 'https://apofiz.com/media/'
CELERY_BROKER_URL = 'amqp://localhost:5672'

