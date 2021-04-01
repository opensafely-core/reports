from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import UserProfile


@receiver(post_save, sender=User)
def ensure_user_profile(sender, instance, created, *args, **kwargs):
    if not hasattr(instance, "profile"):
        UserProfile.objects.create(user=instance)
