"""
URL configuration for lrhub project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings 
from django.conf.urls.static import static 
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', views.home, name='home'),
    path('admin/logout/', LogoutView.as_view(next_page='/admin/login/')),
    path('admin/', admin.site.urls),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),

    #path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/', include('accounts.urls')), 
    path('resources/', include('resources.urls')),
    path('collaboration/', include('collaboration.urls')), 
    path('analytics/', include('analytics.urls')),
    path('api/accounts/', include('accounts.urls')),   # accounts app routes
    path('api/resources/', include('resources.urls')), # resources app routes
    path('api/collaboration/', include('collaboration.urls')), # collaboration routes
    path('api/analytics/', include('analytics.urls')), # analytics app routes
]
if settings.DEBUG: 
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)