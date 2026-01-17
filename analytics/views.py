from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from accounts.models import Profile
from resources.models import Note, StudentResource, Rating, Recommendation
from collaboration.models import Group
from analytics.models import ActivityLog
from django.db.models import Count, Avg, Q

def analytics_home(request):
    return render(request, "analytics/home.html")

def global_analytics(request):
    student_count = Profile.objects.filter(role="student").count()
    teacher_count = Profile.objects.filter(role="teacher").count()

    # ✅ Most downloaded notes/resources (top 2)
    most_downloaded_notes = Note.objects.order_by("-downloads")[:2]
    most_downloaded_resources = StudentResource.objects.order_by("-downloads")[:2]

    # ✅ Highest rated notes/resources (top 2)
    top_notes = Note.objects.annotate(avg_rating=Avg("ratings__value")).order_by("-avg_rating")[:2]
    top_resources = StudentResource.objects.annotate(avg_rating=Avg("ratings__value")).order_by("-avg_rating")[:2]

    group_count = Group.objects.count()

    return render(request, "analytics/global_analytics.html", {
        "student_count": student_count,
        "teacher_count": teacher_count,
        "most_downloaded_notes": most_downloaded_notes,
        "most_downloaded_resources": most_downloaded_resources,
        "top_notes": top_notes,
        "top_resources": top_resources,
        "group_count": group_count,
    })

@login_required
def student_analytics(request):
    # ✅ Student’s own uploaded resources with average rating
    my_resources = StudentResource.objects.filter(uploaded_by=request.user).annotate(
        avg_rating=Avg("ratings__value")
    )

    # ✅ Recommendations given to the student’s resources
    my_resource_recommendations = Recommendation.objects.filter(resource__in=my_resources)

    # ✅ Last 10 activities by the student (actions they performed)
    logs = ActivityLog.objects.filter(
        user=request.user,
        action__in=[
            "note_download",
            "resource_download",
            "rating",
            "recommendation",
            "login",
            "logout",
            "edit_profile",
            "group_post",
            "comment",
            "message"
        ]
    ).order_by("-timestamp")[:10]

    return render(request, "analytics/student_analytics.html", {
        "my_resources": my_resources,
        "my_resource_recommendations": my_resource_recommendations,
        "logs": logs,
    })


@login_required
def teacher_analytics(request):
    my_notes = Note.objects.filter(uploaded_by=request.user)

    ratings = Rating.objects.filter(Q(note__in=my_notes))
    recommendations = Recommendation.objects.filter(Q(note__in=my_notes))

    # ✅ Last 10 teacher activities (upload, verification, login, logout)
    my_activity = ActivityLog.objects.filter(
        user=request.user,
        action__in=["group_post", "note_upload", "resource_upload", "verification", "login", "logout"]
    ).order_by("-timestamp")[:10]

    return render(request, "analytics/teacher_analytics.html", {
        "my_notes": my_notes,
        "ratings": ratings,
        "recommendations": recommendations,
        "my_activity": my_activity,
    })
