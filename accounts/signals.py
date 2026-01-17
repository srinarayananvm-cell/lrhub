from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile

# Create profile only if it doesn't exist
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        # Do not force role here — let SignupForm.save() set it
        Profile.objects.get_or_create(user=instance)

# Delete file when Profile is deleted
@receiver(post_delete, sender=Profile)
def delete_avatar_on_profile_delete(sender, instance, **kwargs):
    if instance.avatar:
        instance.avatar.delete(save=False)

# Delete old avatar file when avatar is cleared or replaced
@receiver(pre_save, sender=Profile)
def delete_old_avatar_on_change(sender, instance, **kwargs):
    if not instance.pk:
        return  # new profile, nothing to clean yet

    try:
        old_avatar = Profile.objects.get(pk=instance.pk).avatar
    except Profile.DoesNotExist:
        return

    # If avatar is being cleared or replaced
    if old_avatar and old_avatar != instance.avatar:
        old_avatar.delete(save=False)
