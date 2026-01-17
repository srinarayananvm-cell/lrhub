from django.urls import path
from .views import resources_home

urlpatterns = [
    path('', resources_home, name='resources_home'),
]
