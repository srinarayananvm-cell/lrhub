from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse

class CustomSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Switch cookie name based on path
        if request.path.startswith('/admin/'):
            settings.SESSION_COOKIE_NAME = "admin_sessionid"
        else:
            settings.SESSION_COOKIE_NAME = "user_sessionid"

        response = self.get_response(request)
        return response

class BlockAdminFromMainSiteMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # If superuser tries to access non-admin URLs
        if request.user.is_authenticated and request.user.is_superuser:
            if not request.path.startswith(reverse('admin:index')):
                return redirect('/admin/')  # force them back to admin
        return self.get_response(request)
