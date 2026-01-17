from django import forms
from .models import Group, Post, Comment,Message

class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ["name", "description"]

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["title", "content"]

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["content"]
class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ["content"]
        widgets = {
            "content": forms.TextInput(attrs={"class": "form-control", "placeholder": "Type your message..."})
        }
