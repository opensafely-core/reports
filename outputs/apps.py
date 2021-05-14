import requests_cache
from django.apps import AppConfig
from environs import Env


env = Env()


class OutputsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "outputs"


requests_cache.install_cache(env.str("REQUESTS_CACHE_NAME"), backend="sqlite")
