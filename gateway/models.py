import structlog
from django.contrib.auth.models import AbstractUser
from django.db import models


logger = structlog.getLogger()


class Organisation(models.Model):
    """An NHS Organisation"""

    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.code} - {self.name}"


class User(AbstractUser):
    organisations = models.ManyToManyField(Organisation, blank=True)
    title = models.CharField(max_length=50, null=True, blank=True)
    display_name = models.CharField(max_length=255)

    def get_full_name(self):
        return self.display_name

    def save(self, *args, **kwargs):
        if not self.id:
            logger.info("User created", username=self.username)
        return super().save(*args, **kwargs)
