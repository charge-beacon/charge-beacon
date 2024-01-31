"""
Django settings for charging project.

Generated by 'django-admin startproject' using Django 5.0.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""

import os
from pathlib import Path
from celery.schedules import crontab

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY-', 'django-insecure-59o*(8*%1r5dcx0r1oq=yu5$-c(vk^5zqexiiywgj847eevx_1')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DEBUG", "false") == "true"

APP_NAME = os.environ.get("FLY_APP_NAME")
ALLOWED_HOSTS = [f'{APP_NAME}.fly.dev', 'www.chargebeacon.app', 'chargebeacon.app']
CSRF_TRUSTED_ORIGINS = [f'https://{host}' for host in ALLOWED_HOSTS]

if DEBUG:
    ALLOWED_HOSTS.append("127.0.0.1")
    INTERNAL_IPS = [
        '127.0.0.1',
    ]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.humanize',
    'django.contrib.gis',
    'debug_toolbar',
    'simple_history',
    'plausible_proxy',
    'django_bootstrap5',
    'crispy_forms',
    'crispy_bootstrap5',
    'django_registration',
    'anymail',
    'django_countries',
    'django_celery_results',
    'mjml',
    'accounts',
    'app',
    'beacon'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware',
]

ROOT_URLCONF = 'charging.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['accounts/templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'app.context_processors.site',
                'beacon.context_processors.searches'
            ],
        },
    },
]

WSGI_APPLICATION = 'charging.wsgi.application'

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

if 'DATABASE_URL' in os.environ:
    import dj_database_url

    DATABASES['default'] = dj_database_url.config(
        engine='django.contrib.gis.db.backends.postgis',
        conn_max_age=600,
    )

CELERY_BROKER_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/")
CELERY_RESULT_BACKEND = "django-db"
CELERY_RESULT_EXTENDED = True

CELERY_BEAT_SCHEDULE = {
    'sync_fuel_stations_every_15_min': {
        'task': 'app.tasks.sync_fuel_stations',
        'schedule': crontab(minute='*/15'),
    },
    'schedule_daily_rollup_emails': {
        'task': 'beacon.tasks.create_daily_rollup_emails',
        'schedule': crontab(minute='0', hour='0'),
    },
    'schedule_weekly_rollup_emails': {
        'task': 'beacon.tasks.create_weekly_rollup_emails',
        'schedule': crontab(minute='0', hour='6', day_of_week='mon'),
    },
}

# Caching

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.environ.get("REDIS_URL", "redis://localhost:6379"),
    }
}

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = 'static/'

STATIC_ROOT = 'staticfiles/'

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

SITE_ID = 1

NREL_API_KEY = os.environ.get('NREL_API_KEY', '')

PLAUSIBLE_SCRIPT_PREFIX = 'plsbl/js'

if SENTRY_DSN := os.environ.get('SENTRY_DSN', None):
    import sentry_sdk

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
    )

BOOTSTRAP5 = {
    "css_url": {
        "url": "https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css",
        "integrity": "sha384-T3c6CoIi6uLrA9TneNEoa7RxnatzjcDSCmG1MXxSR1GAsXEV/Dwwykc2MPK8M2HN",
        "crossorigin": "anonymous",
    },
    "javascript_url": {
        "url": "https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js",
        "integrity": "sha384-C6RzsynM9kWDrMNeT87bh95OGNyZPhcTNXj1NW7RuBCsyN/o0jlpcV8Qyq46cDfL",
        "crossorigin": "anonymous",
    }
}

CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

APPEND_SLASH = False
LOGIN_URL = '/accounts/login'
LOGIN_REDIRECT_URL = '/profile'
LOGOUT_REDIRECT_URL = '/'

ACCOUNT_ACTIVATION_DAYS = 7

ANYMAIL = {
    "MAILGUN_API_KEY": os.environ.get('MAILGUN_API_KEY', ''),
    "MAILGUN_SENDER_DOMAIN": os.environ.get('MAILGUN_SENDER_DOMAIN', ''),
}

if ANYMAIL['MAILGUN_API_KEY'] and ANYMAIL['MAILGUN_SENDER_DOMAIN']:
    EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"
    DEFAULT_FROM_EMAIL = f"no-reply@{ANYMAIL['MAILGUN_SENDER_DOMAIN']}"
    SERVER_EMAIL = f"server@{ANYMAIL['MAILGUN_SENDER_DOMAIN']}"
else:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = os.environ.get('EMAIL_HOST', 'localhost')
    EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 1025))
    DEFAULT_FROM_EMAIL = 'no-reply@localhost'

MJML_BACKEND_MODE = 'cmd'
MJML_EXEC_CMD = BASE_DIR / 'node_modules/mjml/bin/mjml'
