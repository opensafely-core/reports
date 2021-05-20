from django.apps import AppConfig
from environs import Env


env = Env()


class OutputsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "outputs"
