from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q, Avg
from .models import Profile
from .forms import SignupForm, LoginForm, ProfileForm, UserEditForm, ProfileEditForm
from resources.models import Note, StudentResource, Rating, Recommendation
from resources.forms import NoteForm, StudentResourceForm, RatingForm, RecommendationForm
from django.http import FileResponse, JsonResponse
from analytics.models import ActivityLog
from .utils import extract_pdf_text, relevance_score
from django.contrib.auth.decorators import user_passes_test
import pandas as pd
# --- Auth Page (combined login/signup tabs) ---
def auth_page(request):
    signup_form = SignupForm()
    login_form = LoginForm()
    return render(request, 'accounts/auth.html', {
        'signup_form': signup_form,
        'login_form': login_form,
    })
# --- Signup ---
def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            profile = user.profile

            if profile.role == "teacher" and not profile.approved:
                # 🚫 Do NOT log in teacher
                messages.warning(request, "Your teacher account is awaiting admin approval before you can log in.")
                return render(request, "accounts/pending_approval.html")

            # ✅ Students/Admins: safe to auto-login
            login(request, user)  # only one backend, no need to specify
            messages.success(request, "Signup successful! Welcome.")
            return redirect("role_redirect")
    else:
        form = SignupForm()
    return render(request, "accounts/auth.html", {
        "signup_form": form,
        "login_form": LoginForm()
    })
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            profile = getattr(user, "profile", None)

            # 🚫 Block unapproved teachers before login
            if profile and profile.role == "teacher" and not profile.approved:
                messages.error(request, "Your teacher account is awaiting admin approval. You cannot log in yet.")
                return render(request, "accounts/pending_approval.html")

            # ✅ Safe to log in students/admins/approved teachers
            login(request, user)  # only one backend now
            messages.success(request, "Login successful!")
            return redirect("role_redirect")
    else:
        form = LoginForm()

    return render(request, "accounts/auth.html", {
        "login_form": form,
        "signup_form": SignupForm()
    })
def pending_approval(request):
    return render(request, "accounts/pending_approval.html")

# --- Logout ---
def logout_view(request):
    if request.method == 'POST':
        logout(request)
        messages.info(request, "You have logged out.")
        return redirect('home')


# --- Role Redirect ---
@login_required
def role_redirect(request):
    profile = Profile.objects.get(user=request.user)

    if request.user.is_superuser:
        return redirect('admin_dashboard')
    elif profile.role == 'teacher':
        return redirect('teacher_dashboard')
    elif profile.role == 'student':
        return redirect('student_dashboard')
    else:
        messages.error(request, "Role not assigned. Contact admin.")
        return redirect('home')

@login_required
def teacher_dashboard(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    # Block superusers
    if request.user.is_superuser:
        messages.error(request, "Admins cannot access the teacher dashboard.")
        return redirect('/admin/')

    # Block non-teachers
    if profile.role != 'teacher':
        messages.error(request, "Only teachers can access this dashboard.")
        return redirect('home')
    if not profile.approved: 
        return render(request, "accounts/pending_approval.html") 

    # Profile edit
    if request.method == 'POST' and 'edit_profile' in request.POST:
        form = ProfileForm(request.POST, request.FILES, instance=profile, user=request.user)
        if form.is_valid():
            form.save(user=request.user)   # ✅ saves User.email + Profile fields
            messages.success(request, "Profile updated successfully!")
            return redirect('teacher_dashboard')
    else:
        form = ProfileForm(instance=profile, user=request.user)

    # Note upload
    note_form = NoteForm()
    if request.method == 'POST' and 'upload_note' in request.POST:
        note_form = NoteForm(request.POST, request.FILES)
        if note_form.is_valid():
            note = note_form.save(commit=False)
            note.uploaded_by = request.user
            note.save()
            messages.success(request, "Note uploaded successfully!")
            return redirect('teacher_dashboard')

    # Teacher’s own notes
    notes = list(Note.objects.filter(uploaded_by=request.user))
    for n in notes:
        n.my_rating = Rating.objects.filter(user=request.user, note=n).first()

    # Delete educator note (Notes tab, only if uploaded_by is teacher)
    if request.method == 'POST' and 'delete_note' in request.POST:
        note_id = request.POST.get('note_id')
        note = Note.objects.filter(id=note_id, uploaded_by=request.user).first()
        if note:
            note.delete()
            messages.success(request, "Your note was deleted successfully!")
        else:
            messages.error(request, "You can only delete your own notes.")
        return redirect(f"{request.path}?tab=notes")


    # Recommendations (fetch ALL so updates show immediately)
    note_recommendations = Recommendation.objects.filter(note__isnull=False)

    # Ratings for notes
    if request.method == 'POST' and 'rate_note' in request.POST:
        note_id = request.POST.get('note_id')
        rating_form = RatingForm(request.POST)
        if rating_form.is_valid() and note_id:
            Rating.objects.update_or_create(
                note_id=int(note_id),
                user=request.user,
                defaults={'value': rating_form.cleaned_data['value']}
            )
            messages.success(request, "Your rating has been saved!")
            return redirect(f"{request.path}?tab=notes")
    else:
        rating_form = RatingForm()

    # Recommendations for notes
    show_recommend_form_ids = set()
    if request.method == 'POST' and 'recommend_note' in request.POST:
        note_id = request.POST.get('note_id')
        recommendation_form = RecommendationForm(request.POST)
        if recommendation_form.is_valid() and note_id:
            Recommendation.objects.update_or_create(
                note_id=int(note_id),
                user=request.user,
                defaults={'comment': recommendation_form.cleaned_data['comment']}
            )
            messages.success(request, "You recommended this note!")
            return redirect(f"{request.path}?tab=notes")
        else:
            if note_id:
                show_recommend_form_ids.add(f"note-{note_id}")
    else:
        recommendation_form = RecommendationForm()

    # 🔎 Search Student Resources (teacher only, no ratings)
    query = request.GET.get('q')
    resource_results = None
    active_tab = request.GET.get('tab', 'profile')

    if query:
        resource_results = list(StudentResource.objects.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        ))
        active_tab = 'search'

    # Handle verification
    if request.method == 'POST' and 'verify_resource' in request.POST:
        res_id = request.POST.get('resource_id')
        StudentResource.objects.filter(id=res_id).update(verified=True)
        messages.success(request, "Resource verified successfully!")
        return redirect(f"{request.path}?tab=search")

    return render(request, 'accounts/teacher_dashboard.html', {
        'profile': profile,
        'form': form,
        'note_form': note_form,
        'notes': notes,
        'rating_form': rating_form,
        'recommendation_form': recommendation_form,
        'note_recommendations': note_recommendations,
        'show_recommend_form_ids': show_recommend_form_ids,
        'query': query,
        'resource_results': resource_results,
        'active_tab': active_tab,
    })

@login_required
def student_dashboard(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    # Block superusers
    if request.user.is_superuser:
        messages.error(request, "Admins cannot access the student dashboard.")
        return redirect('/admin/')

    # Block non-students
    if profile.role != 'student':
        messages.error(request, "Only students can access this dashboard.")
        return redirect('home')

    # Profile edit
    if request.method == 'POST' and 'edit_profile' in request.POST:
        form = ProfileForm(request.POST, request.FILES, instance=profile, user=request.user)
        if form.is_valid():
            form.save(user=request.user)
            messages.success(request, "Profile updated successfully!")
            return redirect(f"{request.path}?tab=profile")
    else:
        form = ProfileForm(instance=profile, user=request.user)

    # Resource upload (My Resources tab)
    resource_form = StudentResourceForm()
    if request.method == 'POST' and 'upload_resource' in request.POST:
        resource_form = StudentResourceForm(request.POST, request.FILES)
        if resource_form.is_valid():
            resource = resource_form.save(commit=False)
            resource.uploaded_by = request.user
            resource.save()
            messages.success(request, "Your resource was shared successfully!")
            return redirect(f"{request.path}?tab=my_resources")

    # My uploads
    my_resources = StudentResource.objects.filter(uploaded_by=request.user)
    # Delete student resource (My Resources tab)
    if request.method == 'POST' and 'delete_resource' in request.POST:
        res_id = request.POST.get('resource_id')
        resource = StudentResource.objects.filter(id=res_id, uploaded_by=request.user).first()
        if resource:
            resource.delete()
            messages.success(request, "Your resource was deleted successfully!")
        else:
            messages.error(request, "You can only delete your own resources.")
        return redirect(f"{request.path}?tab=my_resources")

    # Default: top 2 highly rated notes/resources
    top_notes = Note.objects.annotate(avg=Avg('ratings__value')).order_by('-avg', '-uploaded_at')[:2]
    top_resources = StudentResource.objects.annotate(avg=Avg('ratings__value')).order_by('-verified', '-avg', '-uploaded_at')[:2]

    # Attach my_rating
    for n in top_notes:
        n.my_rating = Rating.objects.filter(user=request.user, note=n).first()
    for r in top_resources:
        r.my_rating = Rating.objects.filter(user=request.user, resource=r).first()
    for r in my_resources:
        r.my_rating = Rating.objects.filter(user=request.user, resource=r).first()

    # Recommendations (fetch ALL so updates show immediately)
    note_recommendations = Recommendation.objects.filter(note__isnull=False)
    res_recommendations = Recommendation.objects.filter(resource__isnull=False)

    # Ratings
    if request.method == 'POST' and 'rate_note' in request.POST:
        note_id = request.POST.get('note_id')
        rating_form = RatingForm(request.POST)
        if rating_form.is_valid() and note_id:
            Rating.objects.update_or_create(
                note_id=int(note_id),
                user=request.user,
                defaults={'value': rating_form.cleaned_data['value']}
            )
            messages.success(request, "Your rating has been saved!")
            query = request.GET.get('q') or request.POST.get('q')
            return redirect(
                f"{request.path}?tab=notes&q={query}" if query else f"{request.path}?tab=notes"
            )

    elif request.method == 'POST' and 'rate_item' in request.POST:
        res_id = request.POST.get('resource_id')
        rating_form = RatingForm(request.POST)
        if rating_form.is_valid() and res_id:
            Rating.objects.update_or_create(
                resource_id=int(res_id),
                user=request.user,
                defaults={'value': rating_form.cleaned_data['value']}
            )
            messages.success(request, "Your rating has been saved!")
            query = request.GET.get('q') or request.POST.get('q') 
            return redirect(
                f"{request.path}?tab=resources&q={query}" if query else f"{request.path}?tab=resources"
            )
    else:
        rating_form = RatingForm()

    # Recommendations
    if request.method == 'POST' and 'recommend_note' in request.POST:
        note_id = request.POST.get('note_id')
        recommendation_form = RecommendationForm(request.POST)
        if recommendation_form.is_valid() and note_id:
            Recommendation.objects.update_or_create(
                note_id=int(note_id),
                user=request.user,
                defaults={'comment': recommendation_form.cleaned_data['comment']}
            )
            messages.success(request, "You recommended this note!")
            query = request.GET.get('q') or request.POST.get('q')
            return redirect(
                f"{request.path}?tab=notes&q={query}" if query else f"{request.path}?tab=notes"
            )
    elif request.method == 'POST' and 'recommend_item' in request.POST:
        res_id = request.POST.get('resource_id')
        recommendation_form = RecommendationForm(request.POST)
        if recommendation_form.is_valid() and res_id:
            Recommendation.objects.update_or_create(
                resource_id=int(res_id),
                user=request.user,
                defaults={'comment': recommendation_form.cleaned_data['comment']}
            )
            messages.success(request, "You recommended this resource!")
            query = request.GET.get('q') or request.POST.get('q')
            return redirect(
                f"{request.path}?tab=resources&q={query}" if query else f"{request.path}?tab=resources"
            )
    else:
        recommendation_form = RecommendationForm()

    # Search
    query = request.GET.get('q')
    note_results = None
    resource_results = None
    active_tab = request.GET.get('tab', 'profile')

    if query and active_tab == 'notes':
        note_results = Note.objects.filter(Q(title__icontains=query) | Q(topic__icontains=query))
        for n in note_results:
            n.my_rating = Rating.objects.filter(user=request.user, note=n).first()

    if query and active_tab == 'resources':
        resource_results = StudentResource.objects.filter(Q(title__icontains=query) | Q(description__icontains=query))
        for r in resource_results:
            r.my_rating = Rating.objects.filter(user=request.user, resource=r).first()

    return render(request, 'accounts/student_dashboard.html', {
        'profile': profile,
        'form': form,
        'resource_form': resource_form,
        'my_resources': my_resources,
        'top_notes': top_notes,
        'top_resources': top_resources,
        'note_results': note_results,
        'resource_results': resource_results,
        'rating_form': rating_form,
        'recommendation_form': recommendation_form,
        'note_recommendations': note_recommendations,
        'res_recommendations': res_recommendations,
        'query': query,
        'active_tab': active_tab,
    })
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from analytics.models import ActivityLog
import requests
from io import BytesIO
from PyPDF2 import PdfReader

@login_required
def download_note(request, note_id):
    note = get_object_or_404(Note, id=note_id)

    # increment counter
    note.downloads += 1
    note.save()

    # log in analytics
    ActivityLog.objects.create(
        user=request.user,
        action="note_download",
        description=f"Downloaded note: {note.title}"
    )

    # redirect to Cloudinary URL
    return redirect(note.file.url)


@login_required
def download_student_resource(request, resource_id):
    resource = get_object_or_404(StudentResource, id=resource_id)

    # increment counter
    resource.downloads += 1
    resource.save()

    # log in analytics
    ActivityLog.objects.create(
        user=request.user,
        action="resource_download",
        description=f"Downloaded resource: {resource.title}"
    )

    # redirect to Cloudinary URL
    return redirect(resource.file.url)


def extract_pdf_text_from_url(url):
    response = requests.get(url)
    pdf_file = BytesIO(response.content)
    reader = PdfReader(pdf_file)
    return " ".join(page.extract_text() for page in reader.pages if page.extract_text())


@login_required
def analyze_note(request, note_id):
    note = get_object_or_404(Note, id=note_id)
    query = request.GET.get("query", "").strip()

    if not query:
        return JsonResponse({"error": "Query parameter is required"}, status=400)

    try:
        text = extract_pdf_text_from_url(note.file.url)
        relevance = relevance_score(text, query)
        suggestion = "related" if relevance["score"] >= 20 else "not related"

        return JsonResponse({
            "type": "Note",
            "id": note_id,
            "title": note.title,
            "relevance_score": relevance["score"],
            "best_match": relevance["match"],
            "suggestion": suggestion
        })
    except Exception as e:
        return JsonResponse({"error": f"Analysis failed: {str(e)}"}, status=500)


@login_required
def analyze_resource(request, resource_id):
    resource = get_object_or_404(StudentResource, id=resource_id)
    query = request.GET.get("query", "").strip()

    if not query:
        return JsonResponse({"error": "Query parameter is required"}, status=400)

    try:
        text = extract_pdf_text_from_url(resource.file.url)
        relevance = relevance_score(text, query)
        suggestion = "related" if relevance["score"] >= 20 else "not related"

        return JsonResponse({
            "type": "StudentResource",
            "id": resource_id,
            "title": resource.title,
            "relevance_score": relevance["score"],
            "best_match": relevance["match"],
            "suggestion": suggestion
        })
    except Exception as e:
        return JsonResponse({"error": f"Analysis failed: {str(e)}"}, status=500)

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.auth.views import PasswordResetView

class CustomPasswordResetView(PasswordResetView):
    def send_mail(self, subject_template_name, email_template_name,
                  context, from_email, to_email, html_email_template_name=None):
        subject = render_to_string(subject_template_name, context).strip()
        text_content = render_to_string("accounts/password_reset_email.txt", context)
        html_content = render_to_string("accounts/password_reset_email.html", context)

        msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
        msg.attach_alternative(html_content, "text/html")
        msg.send()


from rest_framework import generics
from .serializers import SignupSerializer

class SignupView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = SignupSerializer

from django.contrib.auth.decorators import user_passes_test

# ✅ Only superusers can access
@user_passes_test(lambda u: u.is_superuser)
def admin_dashboard(request):
    query = request.GET.get("q")
    users = None
    if query:
        users = User.objects.filter(username__icontains=query).select_related("profile")
    return render(request, "accounts/admin_dashboard.html", {"users": users, "query": query})
@user_passes_test(lambda u: u.is_superuser)
def add_user(request):
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"User {user.username} has been created successfully.")
            return redirect("admin_dashboard")
    else:
        form = SignupForm()
    return render(request, "accounts/add_user.html", {"form": form})
@user_passes_test(lambda u: u.is_superuser)
def edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    profile = user.profile
    if request.method == "POST":
        form = UserEditForm(request.POST, instance=user)
        profile_form = ProfileEditForm(request.POST, instance=profile)
        if form.is_valid() and profile_form.is_valid():
            form.save()
            profile_form.save()
            messages.success(request, f"User {user.username} has been updated successfully.")
            return redirect("admin_dashboard")
    else:
        form = UserEditForm(instance=user)
        profile_form = ProfileEditForm(instance=profile)
    return render(
        request,
        "accounts/edit_user.html",
        {"form": form, "profile_form": profile_form, "user": user}
    )
@user_passes_test(lambda u: u.is_superuser)
def approve_teacher(request, user_id):
    user = get_object_or_404(User, id=user_id)
    profile = user.profile

    if profile.role == "teacher":
        profile.approved = True
        profile.save()
        messages.success(request, f"Teacher {user.username} has been approved.")

    # ✅ Redirect back to pending requests page
    return redirect("pending_requests")
@user_passes_test(lambda u: u.is_superuser)
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    username = user.username
    user.delete()
    messages.success(request, f"User {username} has been deleted successfully.")
    return redirect("admin_dashboard")

@user_passes_test(lambda u: u.is_superuser)
def bulk_import_users(request):
    if request.method == "POST" and request.FILES.get("file"):
        file = request.FILES["file"]

        try:
            # Pandas auto-detects CSV vs Excel
            df = pd.read_excel(file) if file.name.endswith(".xlsx") else pd.read_csv(file)

            created_count = 0
            skipped_count = 0
            updated_count = 0

            for _, row in df.iterrows():
                username = str(row.get("username")).strip()
                email = str(row.get("email")).strip()
                role = str(row.get("role", "student")).strip().lower()
                approved = str(row.get("approved", "False")).strip().lower() in ["true", "1", "yes"]
                password1 = str(row.get("password1", "")).strip()
                password2 = str(row.get("password2", "")).strip()

                # 🚫 Skip if passwords don’t match or empty
                if password1 != password2 or not password1:
                    skipped_count += 1
                    continue

                user = User.objects.filter(username=username).first()

                if user:
                    # ✅ Update existing user
                    user.email = email
                    user.set_password(password1)
                    user.save()

                    # ✅ Update profile created by signal
                    if hasattr(user, "profile"):
                        user.profile.role = role
                        user.profile.approved = approved
                        user.profile.save()
                    updated_count += 1
                else:
                    # ✅ Create new user (signal will auto-create profile)
                    user = User(username=username, email=email)
                    user.set_password(password1)
                    user.save()

                    # ✅ Update profile created by signal
                    if hasattr(user, "profile"):
                        user.profile.role = role
                        user.profile.approved = approved
                        user.profile.save()
                    created_count += 1

            messages.success(
                request,
                f"{created_count} users created, {updated_count} updated, {skipped_count} skipped."
            )
        except Exception as e:
            messages.error(request, f"Import failed: {e}")

        return redirect("admin_dashboard")

    return render(request, "accounts/bulk_import.html")

def analysis_page_note(request, note_id):
    note = Note.objects.get(id=note_id)
    query = request.GET.get("q", "")
    return render(request, "accounts/analysis_note.html", {"note": note, "query": query})

def analysis_page_resource(request, resource_id):
    resource = StudentResource.objects.get(id=resource_id)
    query = request.GET.get("q", "")
    return render(request, "accounts/analysis_resource.html", {"resource": resource, "query": query})

def pending_requests(request):
    # Only teachers who are not approved yet
    pending_teachers = Profile.objects.filter(role="teacher", approved=False)
    return render(request, "accounts/pending_requests.html", {
        "pending_teachers": pending_teachers
    })
