from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import Profile

# --- Inline Profile editor ---
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'

class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return []
        return super().get_inline_instances(request, obj)

# --- Re-register User with our custom admin ---
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# --- Profile editing separately (optional) ---
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'user_email')   # ✅ fixed: show User.email
    search_fields = ('user__username', 'phone', 'user__email')
    fields = ('user', 'phone', 'bio', 'avatar')      # ✅ removed duplicate email field

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'

# --- Remove "View site" link from admin navbar ---
admin.site.site_url = None

# --- Optional: Customize admin branding ---
admin.site.site_header = "ArivuVerse Administration"
admin.site.site_title = "AV Admin"
admin.site.index_title = "Admin Dashboard"
