from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q, Avg
from .models import Profile
from .forms import SignupForm, LoginForm, ProfileForm
from resources.models import Note, StudentResource, Rating, Recommendation
from resources.forms import NoteForm, StudentResourceForm, RatingForm, RecommendationForm
from django.shortcuts import render, get_object_or_404
from django.http import FileResponse
from django.contrib.auth.decorators import login_required
from analytics.models import ActivityLog
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
            login(request, user)   # auto-login after signup
            messages.success(request, "Signup successful! Welcome.")
            return redirect('role_redirect')
    else:
        form = SignupForm()
    return render(request, 'accounts/auth.html', {
        'signup_form': form,
        'login_form': LoginForm()
    })


# --- Login ---
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, "Login successful!")
            return redirect('role_redirect')
    else:
        form = LoginForm()
    return render(request, 'accounts/auth.html', {
        'login_form': form,
        'signup_form': SignupForm()
    })


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
        return redirect('/admin/')
    elif profile.role == 'teacher':
        return redirect('teacher_dashboard')
    elif profile.role == 'student':
        return redirect('student_dashboard')
    else:
        messages.error(request, "Role not assigned. Contact admin.")
        return redirect('home')
# --- Learners List ---
def learners_only(request):
    users = User.objects.filter(is_staff=False, is_superuser=False)
    return render(request, 'accounts/users_list.html', {'users': users})

def learners_list(request):
    learners = Profile.objects.filter(role='student')
    return render(request, 'accounts/learners_list.html', {'learners': learners})


# --- Profile ---
@login_required
def profile_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    return render(request, 'accounts/profile.html', {'profile': profile})

@login_required
def edit_profile(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile, user=request.user)
        if form.is_valid():
            form.save(user=request.user)
            messages.success(request, "Profile updated successfully!")
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile, user=request.user)
    return render(request, 'accounts/edit_profile.html', {'form': form})

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

@login_required
def download_note(request, note_id):
    note = get_object_or_404(Note, id=note_id)

    # ✅ increment counter
    note.downloads += 1
    note.save()

    # ✅ log in analytics
    ActivityLog.objects.create(
        user=request.user,
        action="note_download",
        description=f"Downloaded note: {note.title}"
    )

    # ✅ stream file
    return FileResponse(note.file.open(), as_attachment=True, filename=note.file.name)
@login_required
def download_student_resource(request, resource_id):
    resource = get_object_or_404(StudentResource, id=resource_id)

    # ✅ increment counter
    resource.downloads += 1
    resource.save()

    # ✅ log in analytics
    ActivityLog.objects.create(
        user=request.user,
        action="resource_download",
        description=f"Downloaded resource: {resource.title}"
    )

    # ✅ stream file
    return FileResponse(resource.file.open(), as_attachment=True, filename=resource.file.name)

from rest_framework import generics
from django.contrib.auth.models import User
from .serializers import SignupSerializer

class SignupView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = SignupSerializer
