"""
Django settings for output_explorer project.

Generated by 'django-admin startproject' using Django 3.1.7.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""
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

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_extensions",
    "social_django",
    "gateway",
    "outputs",
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
    "social_django.middleware.SocialAuthExceptionMiddleware",
]

ROOT_URLCONF = "output_explorer.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": ["templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "social_django.context_processors.backends",
                "social_django.context_processors.login_redirect",
                "gateway.context_processors.show_login",
                "outputs.context_processors.outputs",
            ],
        },
    },
]

WSGI_APPLICATION = "output_explorer.wsgi.application"


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

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static", BASE_DIR / "dist"]
STATIC_ROOT = BASE_DIR / "collected-static"

# Insert Whitenoise Middleware.
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
WHITENOISE_KEEP_ONLY_HASHED_FILES = True

# EMAIL
EMAIL_BACKEND = env.str("EMAIL_BACKEND", "django.core.mail.backends.dummy.EmailBackend")

# SOCIAL AUTH

AUTH_USER_MODEL = "gateway.User"

AUTHENTICATION_BACKENDS = (
    "gateway.backends.NHSIDConnectAuth",
    "django.contrib.auth.backends.ModelBackend",
)

LOGIN_ERROR_URL = "/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"
LOGIN_URL = reverse_lazy("gateway:login")

SOCIAL_AUTH_PIPELINE = (
    "social_core.pipeline.social_auth.social_details",
    "social_core.pipeline.social_auth.social_uid",
    "social_core.pipeline.social_auth.social_user",
    "social_core.pipeline.user.get_username",
    # No email validation for now
    # 'social_core.pipeline.mail.mail_validation'
    # 'social_core.pipeline.social_auth.associate_by_email',
    "social_core.pipeline.user.create_user",
    "social_core.pipeline.social_auth.associate_user",
    "social_core.pipeline.social_auth.load_extra_data",
    "social_core.pipeline.user.user_details",
    "gateway.pipeline.update_user_profile",
)

SOCIAL_AUTH_ADMIN_USER_SEARCH_FIELDS = ["username", "first_name", "email"]
SOCIAL_AUTH_NHSID_KEY = env.str("SOCIAL_AUTH_NHSID_KEY")
SOCIAL_AUTH_NHSID_SECRET = env.str("SOCIAL_AUTH_NHSID_SECRET")
SOCIAL_AUTH_NHSID_API_URL = env.str("SOCIAL_AUTH_NHSID_API_URL")
SOCIAL_AUTH_NHSID_USERNAME_KEY = "nhsid_useruid"
SOCIAL_AUTH_NHSID_SCOPE = ["nhsperson", "associatedorgs"]

# Logging
LOGGING = logging_config_dict
initialise_sentry()

# Needed for the debug context processor to work locally
INTERNAL_IPS = ["127.0.0.1"]
