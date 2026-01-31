from django.db import models
from django.contrib.auth.models import User

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
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    approved = models.BooleanField(default=False)  # ✅ new field

    def __str__(self):
        return f"{self.user.username} ({self.role})"

    def save(self, *args, **kwargs):
        # ✅ Just call the parent save — no local disk operations
        super().save(*args, **kwargs)
