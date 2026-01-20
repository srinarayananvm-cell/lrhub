from django.urls import path
from .views import SignupView
from . import views
from django.contrib.auth import views as auth_views
from .views import CustomPasswordResetView

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('signup/', SignupView.as_view(), name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('auth/', views.auth_page, name='auth_page'),
    path('role-redirect/', views.role_redirect, name='role_redirect'),
    path('student-dashboard/', views.student_dashboard, name='student_dashboard'),
    path('teacher-dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path("download/note/<int:note_id>/", views.download_note, name="download_note"),
    path("download/resource/<int:resource_id>/", views.download_student_resource, name="download_student_resource"),
    path("analyze/note/<int:note_id>/", views.analyze_note, name="analyze_note"),
    path("analyze/resource/<int:resource_id>/", views.analyze_resource, name="analyze_resource"),
    path("analysis/note/<int:note_id>/", views.analysis_page_note, name="analysis_page_note"),
    path("analysis/resource/<int:resource_id>/", views.analysis_page_resource, name="analysis_page_resource"),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/add/', views.add_user, name='add_user'),
    path('admin-dashboard/edit/<int:user_id>/', views.edit_user, name='edit_user'),

    path('password_reset/', CustomPasswordResetView.as_view(
        template_name='accounts/password_reset_form.html',
        subject_template_name='accounts/password_reset_subject.txt',
        ), name='password_reset'),

    path('password_reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='accounts/password_reset_done.html'
         ),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='accounts/password_reset_confirm.html'
         ),
         name='password_reset_confirm'),
    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='accounts/password_reset_complete.html'
         ),
         name='password_reset_complete'),

]


