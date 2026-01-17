from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import Note, StudentResource

@receiver(post_delete, sender=Note)
def delete_file_on_note_delete(sender, instance, **kwargs):
    if instance.file:
        instance.file.delete(save=False)

@receiver(post_delete, sender=StudentResource)
def delete_file_on_resource_delete(sender, instance, **kwargs):
    if instance.file:
        instance.file.delete(save=False)
