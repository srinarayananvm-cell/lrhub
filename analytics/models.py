from django.db import models
from django.contrib.auth.models import User

class ActivityLog(models.Model):
    ACTION_CHOICES = [
        ("search", "Search"),
        ("note_download", "Note Downloaded"),
        ("resource_download", "Resource Downloaded"),
        ("rating", "Rating Given"),
        ("recommendation", "Recommendation Made"),
        ("group_create", "Group Created"),
        ("group_post", "Group Post"),
        ("comment", "Comment Added"),
        ("message", "Message Sent"),
        ("login", "User Logged In"),       # ✅ new
        ("logout", "User Logged Out"),     # ✅ new
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    description = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.username} - {self.action} ({self.timestamp:%Y-%m-%d %H:%M})"
