from django.db import models
from django.contrib.auth.models import User
from cloudinary.models import CloudinaryField

class Profile(models.Model):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ("admin", "Admin"),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    phone = models.CharField(max_length=15, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    # ✅ Persist avatars directly in Cloudinary
    avatar = CloudinaryField('image', blank=True, null=True)
    approved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} ({self.role})"
