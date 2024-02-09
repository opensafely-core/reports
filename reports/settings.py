"""
Django settings for reports project.

Generated by 'django-admin startproject' using Django 3.1.7.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""

import re
from pathlib import Path

from django.urls import reverse_lazy
from environs import Env
from furl import furl

from services.logging import logging_config_dict
from services.sentry import initialise_sentry


env = Env()
env.read_env()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.str("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool("DEBUG", False)

BASE_URL = env.str("BASE_URL", default="http://localhost:8000")

ALLOWED_HOSTS = [furl(BASE_URL).host]

# Default to True; may need to be False for local/testing
# SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", True)

# https://docs.djangoproject.com/en/4.0/ref/settings/#std:setting-CSRF_TRUSTED_ORIGINS
CSRF_TRUSTED_ORIGINS = [BASE_URL]

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_vite",
    "django_extensions",
    "gateway",
    "reports",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.cache.UpdateCacheMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.cache.FetchFromCacheMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_structlog.middlewares.RequestMiddleware",
    "csp.middleware.CSPMiddleware",
    "reports.middleware.XSSFilteringMiddleware",
]

ROOT_URLCONF = "reports.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "reports.context_processors.reports",
            ],
        },
    },
]

WSGI_APPLICATION = "reports.wsgi.application"


# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

DATABASES = {"default": env.dj_db_url("DATABASE_URL", "sqlite:///db.sqlite3")}


# Default primary key field type to use for models that don’t have a field with primary_key=True.
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
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


# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/
BUILT_ASSETS = env.path("BUILT_ASSETS", default=BASE_DIR / "assets" / "dist")
STATICFILES_DIRS = [
    str(BASE_DIR / "static"),
    str(BUILT_ASSETS),
]
STATIC_ROOT = env.path("STATIC_ROOT", default=BASE_DIR / "staticfiles")
STATIC_URL = "/static/"

ASSETS_DEV_MODE = env.bool("ASSETS_DEV_MODE", default=False)

DJANGO_VITE = {
    "default": {
        "dev_mode": ASSETS_DEV_MODE,
        "manifest_path": BUILT_ASSETS / ".vite" / "manifest.json",
    }
}

# Vite generates files with 8 hash digits
# http://whitenoise.evans.io/en/stable/django.html#WHITENOISE_IMMUTABLE_FILE_TEST


def immutable_file_test(path, url):
    # Match filename with 12 hex digits before the extension
    # e.g. app.db8f2edc0c8a.js
    return re.match(r"^.+[\.\-][0-9a-f]{8,12}\..+$", url)


WHITENOISE_IMMUTABLE_FILE_TEST = immutable_file_test

# Insert Whitenoise Middleware.
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"


# User uploaded files
# https://docs.djangoproject.com/en/4.1/topics/files/
MEDIA_ROOT = Path(env.str("MEDIA_STORAGE", default="uploads"))
MEDIA_URL = "/uploads/"


# EMAIL
EMAIL_BACKEND = env.str("EMAIL_BACKEND", "django.core.mail.backends.dummy.EmailBackend")

# Auth
AUTH_USER_MODEL = "gateway.User"

LOGIN_ERROR_URL = "/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"
LOGIN_URL = reverse_lazy("admin:login")

# Logging
LOGGING = logging_config_dict
initialise_sentry()

# Needed for the debug context processor to work locally
INTERNAL_IPS = ["127.0.0.1"]

# Caching
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "cache_table",
    }
}


# CSP
# https://django-csp.readthedocs.io/en/latest/configuration.html
CSP_REPORT_ONLY = DEBUG
CSP_DEFAULT_SRC = ["'none'"]

# Duplicate the *_ELEM settings for Firefox
# https://bugzilla.mozilla.org/show_bug.cgi?id=1529338
CSP_STYLE_SRC = CSP_STYLE_SRC_ELEM = ["'self'", "https://fonts.googleapis.com"]
CSP_SCRIPT_SRC = CSP_SCRIPT_SRC_ELEM = ["'self'", "https://plausible.io"]

CSP_CONNECT_SRC = ["https://plausible.io"]
CSP_FONT_SRC = ["'self'", "https://fonts.gstatic.com"]
CSP_IMG_SRC = ["'self'", "data:"]
CSP_MANIFEST_SRC = ["'self'"]

# configure django-csp to work with Vite when using it in dev mode
if ASSETS_DEV_MODE:
    CSP_CONNECT_SRC = ["ws://localhost:5173/static/"]
    CSP_SCRIPT_SRC_ELEM = ["'self'", "http://localhost:5173"]
    CSP_STYLE_SRC_ELEM = ["'self'", "https://fonts.googleapis.com", "'unsafe-inline'"]


# Permissions Policy
# https://github.com/adamchainz/django-permissions-policy/blob/main/README.rst
PERMISSIONS_POLICY = {
    "interest-cohort": [],
}
