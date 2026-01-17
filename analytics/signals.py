from django.db.models.signals import post_save
from collaboration.models import Group, Post, Comment, Message
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from analytics.models import ActivityLog
from resources.models import Rating, Recommendation

# --- Group Creation ---
@receiver(post_save, sender=Group)
def log_group_creation(sender, instance, created, **kwargs):
    if created:
        ActivityLog.objects.create(
            user=instance.created_by,
            action="group_create",   # ✅ distinct action
            description=f"Created group: {instance.name}"
        )

# --- Posts ---
@receiver(post_save, sender=Post)
def log_post(sender, instance, created, **kwargs):
    if created:
        ActivityLog.objects.create(
            user=instance.author,
            action="group_post",
            description=f"Posted in group {instance.group.name}: {instance.title}"
        )

# --- Comments ---
@receiver(post_save, sender=Comment)
def log_comment(sender, instance, created, **kwargs):
    if created:
        ActivityLog.objects.create(
            user=instance.author,
            action="comment",
            description=f"Commented on post '{instance.post.title}': {instance.content[:50]}..."
        )

# --- Messages ---
@receiver(post_save, sender=Message)
def log_message(sender, instance, created, **kwargs):
    if created:
        ActivityLog.objects.create(
            user=instance.author,
            action="message",
            description=f"Message in group {instance.group.name}: {instance.content[:50]}..."
        )
@receiver(user_logged_in)
def log_login(sender, request, user, **kwargs):
    ActivityLog.objects.create(
        user=user,
        action="login",
        description="User logged in"
    )

@receiver(user_logged_out)
def log_logout(sender, request, user, **kwargs):
    ActivityLog.objects.create(
        user=user,
        action="logout",
        description="User logged out"
    )
from resources.models import Rating, Recommendation

# --- Ratings ---
@receiver(post_save, sender=Rating)
def log_rating(sender, instance, created, **kwargs):
    if created:
        target = instance.note if instance.note else instance.resource
        ActivityLog.objects.create(
            user=instance.user,
            action="rating",
            description=f"Rated {target} {instance.value}★"
        )
# --- Recommendations ---
@receiver(post_save, sender=Recommendation)
def log_recommendation(sender, instance, created, **kwargs):
    if created:
        target = instance.note if instance.note else instance.resource
        ActivityLog.objects.create(
            user=instance.user,
            action="recommendation",
            description=f"Recommended {target} — \"{instance.comment[:50]}...\""
        )
