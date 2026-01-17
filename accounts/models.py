from django.db import models
from django.contrib.auth.models import User
from PIL import Image

class Profile(models.Model):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('teacher', 'Teacher'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    phone = models.CharField(max_length=15, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} ({self.role})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.avatar:
            img = Image.open(self.avatar.path)

            # Resize while keeping aspect ratio
            img.thumbnail((120, 120))
            img.save(self.avatar.path)
