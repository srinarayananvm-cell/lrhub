from django.urls import path
from . import views

urlpatterns = [
    path('', views.analytics_home, name='analytics_home'),
    path('global/', views.global_analytics, name='global_analytics'),
    path('student/', views.student_analytics, name='student_analytics'),
    path('teacher/', views.teacher_analytics, name='teacher_analytics'),
]

