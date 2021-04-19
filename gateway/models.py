from django.contrib.auth.models import User
from django.db import models


class Organisation(models.Model):
    """An NHS Organisation"""

    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.code} - {self.name}"


class UserProfile(models.Model):
    """
    Additional information about a User, obtained from the NHS Identity Open ID Connect
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    organisations = models.ManyToManyField(Organisation)
    title = models.CharField(max_length=50, null=True, blank=True)
    display_name = models.CharField(max_length=255)

    def __str__(self):
        return str(self.user)
