from django.contrib import admin
from .models import Group, Post, Comment, Message, ChatClear

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at", "created_by")
    search_fields = ("name", "owner__username")

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "group", "author", "created_at")
    search_fields = ("title", "author__username")
    list_filter = ("group", "created_at")

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("post", "author", "created_at")
    search_fields = ("author__username", "content")
    list_filter = ("created_at", "post")

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("group", "author", "content", "created_at")
    search_fields = ("author__username", "content")
    list_filter = ("group", "created_at")

@admin.register(ChatClear)
class ChatClearAdmin(admin.ModelAdmin):
    list_display = ("user", "group", "cleared_at")
    search_fields = ("user__username", "group__name")
