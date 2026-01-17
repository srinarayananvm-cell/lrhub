from django.urls import path
from . import views

urlpatterns = [
    path("", views.collaboration_home, name="collaboration_home"),
    path("group/<int:pk>/", views.group_detail, name="group_detail"),
    path("group/<int:pk>/edit/", views.edit_group, name="edit_group"),
    path("group/<int:pk>/delete/", views.delete_group, name="delete_group"),

    path("post/<int:pk>/", views.post_detail, name="post_detail"),
    path("post/<int:pk>/edit/", views.edit_post, name="edit_post"),
    path("post/<int:pk>/delete/", views.delete_post, name="delete_post"),

    path("comment/<int:pk>/edit/", views.edit_comment, name="edit_comment"),
    path("comment/<int:pk>/delete/", views.delete_comment, name="delete_comment"),

    path("message/<int:pk>/edit/", views.edit_message, name="edit_message"),
    path("message/<int:pk>/delete/", views.delete_message, name="delete_message"),

    path("create/", views.create_group, name="create_group"),
    path("group/<int:pk>/chat/", views.chat_view, name="chat_view"),
    path("group/<int:pk>/chat/clear/", views.clear_my_chat_view, name="clear_my_chat"),


]

