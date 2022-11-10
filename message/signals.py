from django.db.models.signals import post_save, post_init
from django.dispatch import receiver
from djoser.signals import user_activated

from .models import UserProfile


@receiver(post_save, sender=user_activated)
def create_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

