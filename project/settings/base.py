import json
import os
from distutils.util import strtobool

from corsheaders.defaults import default_headers
from decouple import config, Csv
from django.utils.translation import gettext_lazy as _
from kombu.serialization import registry

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='notasecret')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

# Prometheus Monitoring
MONITORING = config('MONITORING', default=False, cast=bool)

# JSON Logging
JSON_LOGGING = config('JSON_LOGGING', default=False, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv(), default='*')

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
    'django_celery_beat',
    'django_extensions',

    'common.apps.CoreConfig',
    'transactions.apps.TransactionsConfig',
    'organizations.apps.OrganizationsConfig',
    'users.apps.UsersConfig',
    'notifications',
    'shop.apps.ShopConfig',
    'instagram_parsers.apps.InstagramParsersConfig',

    'rest_framework',
    'rest_framework.authtoken',
    'rest_auth',
    'corsheaders',
    'mapwidgets',
    'imagekit',
    'fcm_django',
    'drf_multiple_model',
    'storages',
    'phonenumber_field',
    'delivery',
    'imports',
    'cors',
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
    'common.middleware.BackendVersionHeaderMiddleware',
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

STATIC_URL = '/internal-static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'internal-static')

STATICFILES_DIRS = ()

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'
MEDIA_UPLOAD_PREFIX = config('DJANGO_MEDIA_UPLOAD_PREFIX', default='/media/')

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
IMAGEKIT_CACHEFILE_NAMER = 'common.utils.imagekit_filename_generator'
IMAGEKIT_SPEC_CACHEFILE_NAMER = IMAGEKIT_CACHEFILE_NAMER
IMAGEKIT_CACHEFILE_DIR = 'cache/images'

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
    'Device-Timestamp',
]

SESSION_COOKIE_SAMESITE = None

CORS_PREFLIGHT_MAX_AGE = 86400

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

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
NIKITA_TEST_MODE = config('NIKITA_TEST_MODE', default=1, cast=int)

SEND_PULSE_GRAND_TYPE = config('SEND_PULSE_GRAND_TYPE')
SEND_PULSE_CLIENT_ID = config('SEND_PULSE_CLIENT_ID')
SEND_PULSE_CLIENT_SECRET = config('SEND_PULSE_CLIENT_SECRET')
SEND_PULSE_LOGIN_URL = config('SEND_PULSE_LOGIN_URL')
SEND_PULSE_SENDER = config('SEND_PULSE_SENDER')
SEND_PULSE_SMS_URL = config('SEND_PULSE_SMS_URL')

OER_APP_ID = config('OER_APP_ID')
OER_CACHE_TIMEOUT = 60 * 60 * 24
OER_BASE_CURRENCY = 'USD'
PROJECT_ENV = config('PROJECT_ENVIRONMENT', default='dev')
if PROJECT_ENV != 'dev':
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
            'LOCATION': config('CACHE_SERVER_URL', default='memcached:11211'),
        }
    }

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

FCM_DRY_RUN_ENABLE = config('FCM_DRY_RUN_ENABLE', default=True, cast=bool)

HOST_URL = config('DJANGO_HOST_URL', default='https://apofiz.com/media/')
CELERY_BROKER_URL = config('CELERY_DSN', default='amqp://localhost:5672')

CELERY_TASK_ROUTES = {
    'imagekit.cachefiles.backends._generate_file': {'queue': 'high'},
    'notifications.tasks.*': {'queue': 'default'},
    'organizations.tasks.parse_instagram_to_shop_items': {'queue': 'insta_high'},
    'organizations.tasks.delete_not_updated_posts_from_instagram': {'queue': 'insta_low'},
    # 'organizations.tasks.delete_old_instagram_posts': {'queue': 'insta_low'},
    # 'organizations.tasks.update_instagram_videos': {'queue': 'insta_video'},
    # 'organizations.tasks.update_media_url_by_user_entering_on_page': {'queue': 'update_insta_video'},
    'organizations.tasks.update_login_device_settings': {'queue': 'update_login_device'},
    'organizations.tasks.delete_expired_video_url': {'queue': 'delete_expired_video'},
    'organizations.tasks.delete_expired_photo_and_posts': {'queue': 'delete_expired_posts'},
}

INSTAGRAM_VIDEO_EXPIRE_DAYS = config('INSTAGRAM_VIDEO_EXPIRE_DAYS', default=1, cast=int)
INSTAGRAM_LOGIN_DEVICE_EXPIRE_DAYS = config('INSTAGRAM_LOGIN_DEVICE_EXPIRE_DAYS', default=1, cast=int)
INSTAGRAM_IMG_EXPIRE_DAYS = config('INSTAGRAM_IMG_EXPIRE_DAYS', default=3, cast=int)
INSTAGRAM_POSTS_UPDATE_BATCH_SIZE = config('INSTAGRAM_POSTS_UPDATE_BATCH_SIZE', default=30, cast=int)
INSTAGRAM_DAYS_TO_KEEP = config('INSTAGRAM_DAYS_TO_KEEP', default=14, cast=int)

if not DEBUG and JSON_LOGGING:
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': True,
        'formatters': {
            'json': {
                '()': 'common.logs.LogFormatter',
                'timestamp': True
            }
        },
        'handlers': {
            'console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'json',
            }
        },
        'loggers': {
            'django.request': {
                'handlers': ['console'],
                'level': 'ERROR',
            },
        }
    }

# Sentry
if not DEBUG:
    SENTRY_DSN = config(
        "SENTRY_DSN", cast=str, default="https://9830f4ac6ea04f83aed2d7b2abdd24e5@o173421.ingest.sentry.io/5733313"
    )
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production,
        traces_sample_rate=1.0,

        # If you wish to associate users to errors (assuming you are using
        # django.contrib.auth) you may enable sending PII data.
        send_default_pii=True
    )

if MONITORING:
    INSTALLED_APPS += ['django_prometheus']
    MIDDLEWARE = \
        ['django_prometheus.middleware.PrometheusBeforeMiddleware'] + \
        MIDDLEWARE + \
        ['django_prometheus.middleware.PrometheusAfterMiddleware']
    DATABASES['default']['ENGINE'] = 'django_prometheus.db.backends.postgis'


MAP_WIDGETS = {
    # "GooglePointFieldWidget": (
    #     ("zoom", 15),
    #     ("mapCenterLocationName", "london"),
    #     ("GooglePlaceAutocompleteOptions", {'componentRestrictions': {'country': 'uk'}}),
    #     ("markerFitZoom", 12),
    # ),
    "GOOGLE_MAP_API_KEY": "AIzaSyBqsPpFSiHwmvV1xz0hqkSWeNLbuChKqg0"
}
