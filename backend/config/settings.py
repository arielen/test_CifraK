import os
from pathlib import Path

import environ

from .schedules import EmailCrontabSchedule

BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env(
    DEBUG=(bool, True),
    SECRET_KEY=(
        str,
        "django-insecure-8u-ym7yr^wf*^x9@d@7#l3vd$f^*@h9tb!6u*o2xtf5dzar59%",
    ),
    ALLOWED_HOSTS=(list, []),
    DB_ENGINE=(str, "django.contrib.gis.db.backends.postgis"),
    DB_NAME=(str, "db_geonews"),
    DB_USER=(str, "postgres"),
    DB_PASSWORD=(str, "password"),
    DB_HOST=(str, "localhost"),
    DB_PORT=(int, 5432),
    DATABASE_URL=(str, "postgres://postgres:password@localhost/db_geonews"),
    CELERY_BROKER_URL=(str, "redis://localhost:6379/0"),
)
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

DEBUG = env("DEBUG")
SECRET_KEY = env("SECRET_KEY")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

# GDAL
# GEOS_LIBRARY_PATH = os.getenv("GEOS_LIBRARY_PATH", "/usr/lib/libgeos_c.so")
# GDAL_LIBRARY_PATH = os.getenv("GDAL_LIBRARY_PATH", "/usr/lib/libgdal.so")


# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",
    "rest_framework",
    "drf_spectacular",
    "django_summernote",
    "constance",
    "constance.backends.database",
    "news",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# DATABASE CONFIG
DATABASES = {"default": env.db()}
DATABASES["default"]["ENGINE"] = env("DB_ENGINE")

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",  # noqa: E501
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# EMAIL
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "localhost"
EMAIL_PORT = 2525
EMAIL_USE_TLS = False
EMAIL_HOST_USER = "admin@localhost.com"
EMAIL_HOST_PASSWORD = "password"

DEFAULT_FROM_EMAIL = "GeoNews & Spots <admin@localhost.com>"


LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = "static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media/")

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# DRF
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}
SPECTACULAR_SETTINGS = {
    "TITLE": "GeoNews API",
    "DESCRIPTION": "API for GeoNews",
    "VERSION": "0.0.1",
    "SERVE_INCLUDE_SCHEMA": False,
}

# Constance
CONSTANCE_BACKEND = "constance.backends.database.DatabaseBackend"
CONSTANCE_CONFIG = {
    "EMAIL_RECIPIENTS": (
        "admin@localhost.com",
        "List of recipients for notifications (separated by commas)",
    ),
    "EMAIL_SUBJECT": ("News for today", "Email subject line for the daily newsletter"),
    "EMAIL_MESSAGE": (
        "Hello, here is the news published today:",
        "The text of the letter.",
    ),
    "EMAIL_SEND_TIME": ("08:00", "Time to send the daily newsletter"),
    "WEATHER_FETCH_INTERVAL": (
        "01:00",
        "Interval between runs of the weather bulletin task",
    ),
}

# Celery
CELERY_BROKER_URL = env("CELERY_BROKER_URL")
CELERY_BEAT_SCHEDULE = {
    "send-daily-news-email": {
        "task": "news.tasks.send_news_email",
        "schedule": EmailCrontabSchedule(),
    },
}
