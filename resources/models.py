from django.db import models
from django.contrib.auth.models import User
from django.db.models import Avg
from cloudinary.models import CloudinaryField

CATEGORY_CHOICES = [
    ("Computer", "Computer"), ("Social", "Social"), ("ML", "Machine Learning"),
    ("AI", "Artificial Intelligence"), ("Science", "Science"), ("History", "History"),
    ("Math", "Mathematics"), ("Physics", "Physics"), ("Chemistry", "Chemistry"),
    ("Biology", "Biology"), ("Economics", "Economics"), ("Politics", "Politics"), 
    ("Geography", "Geography"), ("Philosophy", "Philosophy"), ("Psychology", "Psychology"),
    ("Education", "Education"), ("Engineering", "Engineering"), ("Medicine", "Medicine"),
    ("Law", "Law"), ("Arts", "Arts"), ("Literature", "Literature"),
    ("Music", "Music"), ("Sports", "Sports"), ("Business", "Business"), ("Other", "Other"), 
]

class Note(models.Model):
    title = models.CharField(max_length=200)
    topic = models.CharField(max_length=100)
    version = models.IntegerField(default=1)
    # ✅ Persist PDFs and other files directly in Cloudinary
    file = CloudinaryField('file', resource_type='raw')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, blank=True, null=True)
    downloads = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.title} (v{self.version})"

    def average_rating(self):
        avg = self.ratings.aggregate(Avg('value'))['value__avg']
        return avg or None


class StudentResource(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    # ✅ Persist resources (PDFs, docs, etc.) in Cloudinary
    file = CloudinaryField('file', resource_type='raw')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    verified = models.BooleanField(default=False)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, blank=True, null=True)
    downloads = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.title} by {self.uploaded_by.username}"

    def average_rating(self): 
        avg = self.ratings.aggregate(Avg('value'))['value__avg']
        return avg or None


class Rating(models.Model):
    note = models.ForeignKey(Note, related_name="ratings", on_delete=models.CASCADE, null=True, blank=True)
    resource = models.ForeignKey(StudentResource, related_name="ratings", on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    value = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])  # 1–5 stars
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'note'], name='unique_user_note_rating'),
            models.UniqueConstraint(fields=['user', 'resource'], name='unique_user_resource_rating'),
        ]

    def __str__(self):
        target = self.note if self.note else self.resource
        return f"{self.user.username} rated {target} {self.value}★"


class Recommendation(models.Model):
    note = models.ForeignKey(Note, related_name="recommendations", on_delete=models.CASCADE, null=True, blank=True)
    resource = models.ForeignKey(StudentResource, related_name="recommendations", on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'note'], name='unique_user_note_recommendation'),
            models.UniqueConstraint(fields=['user', 'resource'], name='unique_user_resource_recommendation'),
        ]

    def __str__(self):
        target = self.note if self.note else self.resource
        return f"{self.user.username} recommended {target}"
