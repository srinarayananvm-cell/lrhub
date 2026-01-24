from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth import logout
from django.shortcuts import redirect

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



class TeacherApprovalMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # 🚫 Skip superusers and staff
            if request.user.is_superuser or request.user.is_staff:
                return self.get_response(request)
            profile = getattr(request.user, "profile", None)
            if profile and profile.role == "teacher" and not profile.approved:
                logout(request)
                return redirect("pending_approval")

        return self.get_response(request)
