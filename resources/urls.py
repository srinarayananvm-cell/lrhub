from django.urls import path
from .views import resources_home, search_recommendations, summarize_pdf

urlpatterns = [
    path('', resources_home, name='resources_home'),
    path("search_recommendations/", search_recommendations, name="search_recommendations"),
    path("pdf/<str:type>/<int:pk>/summarize/", summarize_pdf, name="summarize_pdf"),
]
