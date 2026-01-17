from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Group, Post, Comment, Message, ChatClear
from .forms import GroupForm, PostForm, CommentForm, MessageForm
from django.urls import reverse
from django.utils import timezone


def collaboration_home(request):
    """Show all collaboration groups."""
    groups = Group.objects.all()
    return render(request, "collaboration/collaboration_home.html", {"groups": groups})


@login_required
def group_detail(request, pk):
    """Show a single group with its posts and allow new post creation."""
    group = get_object_or_404(Group, pk=pk)
    posts = group.posts.all()

    if request.method == "POST":
        post_form = PostForm(request.POST)
        if post_form.is_valid():
            post = post_form.save(commit=False)
            post.group = group
            post.author = request.user
            post.save()
            return redirect("group_detail", pk=group.pk)
    else:
        post_form = PostForm()

    return render(request, "collaboration/group_detail.html", {
        "group": group,
        "posts": posts,
        "post_form": post_form,
    })


@login_required
def create_group(request):
    """Create a new collaboration group."""
    if request.method == "POST":
        form = GroupForm(request.POST)
        if form.is_valid():
            group = form.save(commit=False)
            group.created_by = request.user
            group.save()
            group.members.add(request.user)  # creator auto joins
            return redirect("collaboration_home")
    else:
        form = GroupForm()
    return render(request, "collaboration/create_group.html", {"form": form})


@login_required
def post_detail(request, pk):
    """Show a single post with its comments and allow new comment creation."""
    post = get_object_or_404(Post, pk=pk)
    comments = post.comments.all()

    if request.method == "POST":
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            return redirect(f"{reverse('post_detail', args=[post.pk])}?show_comments=1")
    else:
        comment_form = CommentForm()

    return render(request, "collaboration/post_detail.html", {
        "post": post,
        "comments": comments,
        "comment_form": comment_form,
    })

@login_required
def chat_view(request, pk):
    group = get_object_or_404(Group, pk=pk)

    # check if user has cleared before
    clear_record = ChatClear.objects.filter(user=request.user, group=group).first()
    if clear_record:
        chat_messages = group.messages.filter(created_at__gt=clear_record.cleared_at).order_by("created_at")
    else:
        chat_messages = group.messages.order_by("created_at")

    if request.method == "POST":
        form = MessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.group = group
            msg.author = request.user
            msg.save()
            return redirect("chat_view", pk=group.pk)  # redirect back to chat after sending
    else:
        form = MessageForm()

    return render(request, "collaboration/chat.html", {
        "group": group,
        "chat_messages": chat_messages,
        "form": form,
    })

# --- GROUPS ---
@login_required
def edit_group(request, pk):
    group = get_object_or_404(Group, pk=pk, created_by=request.user)
    if request.method == "POST":
        form = GroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            return redirect("group_detail", pk=group.pk)
    else:
        form = GroupForm(instance=group)
    return render(request, "collaboration/edit_group.html", {"form": form, "group": group})

@login_required
def delete_group(request, pk):
    group = get_object_or_404(Group, pk=pk, created_by=request.user)
    if request.method == "POST":
        group.delete()
        return redirect("collaboration_home")
    return render(request, "collaboration/confirm_delete.html", {"object": group, "type": "Group"})


# --- POSTS ---
@login_required
def edit_post(request, pk):
    post = get_object_or_404(Post, pk=pk, author=request.user)
    if request.method == "POST":
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            return redirect("group_detail", pk=post.group.pk)
    else:
        form = PostForm(instance=post)
    return render(request, "collaboration/edit_post.html", {"form": form, "post": post})

@login_required
def delete_post(request, pk):
    post = get_object_or_404(Post, pk=pk, author=request.user)
    if request.method == "POST":
        post.delete()
        return redirect("group_detail", pk=post.group.pk)
    return render(request, "collaboration/confirm_delete.html", {"object": post, "type": "Post"})


# --- COMMENTS ---
@login_required
def edit_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk, author=request.user)
    if request.method == "POST":
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect("post_detail", pk=comment.post.pk)
    else:
        form = CommentForm(instance=comment)
    return render(request, "collaboration/edit_comment.html", {"form": form, "comment": comment})

@login_required
def delete_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk, author=request.user)
    if request.method == "POST":
        comment.delete()
        return redirect("post_detail", pk=comment.post.pk)
    return render(request, "collaboration/confirm_delete.html", {"object": comment, "type": "Comment"})


# --- CHAT MESSAGES ---
@login_required
def edit_message(request, pk):
    message = get_object_or_404(Message, pk=pk, author=request.user)
    if request.method == "POST":
        form = MessageForm(request.POST, instance=message)
        if form.is_valid():
            form.save()
            return redirect("chat_view", pk=message.group.pk)
    else:
        form = MessageForm(instance=message)
    return render(request, "collaboration/edit_message.html", {"form": form, "message": message})

@login_required
def delete_message(request, pk):
    message = get_object_or_404(Message, pk=pk, author=request.user)
    if request.method == "POST":
        message.delete()
        return redirect("chat_view", pk=message.group.pk)
    return render(request, "collaboration/confirm_delete.html", {"object": message, "type": "Message"})

@login_required
def clear_my_chat_view(request, pk):
    group = get_object_or_404(Group, pk=pk)

    if request.method == "POST":
        # update or create clear record
        ChatClear.objects.update_or_create(
            user=request.user,
            group=group,
            defaults={"cleared_at": timezone.now()}
        )
        return redirect("chat_view", pk=group.pk)

    return render(request, "collaboration/confirm_clear_chat.html", {"group": group})

