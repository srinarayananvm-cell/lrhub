from django import forms
from .models import Profile
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm


# --- Signup Form ---
class SignupForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Re-enter your password'
        })
    )
    role = forms.ChoiceField(
        choices=[c for c in Profile.ROLE_CHOICES if c[0] != "admin"],  # ✅ hide admin
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Role"
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'role']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Create a username'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your email address'
            }),
        }
        help_texts = {'username': None}

    def clean_password2(self):
        if self.cleaned_data.get("password1") != self.cleaned_data.get("password2"):
            raise forms.ValidationError("Passwords don’t match.")
        return self.cleaned_data.get("password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()

        profile, created = Profile.objects.get_or_create(user=user)
        role = self.cleaned_data.get("role", "student")

        # ✅ Prevent tampering: force student if someone tries "admin"
        if role == "admin":
            role = "student"

        profile.role = role

        # ✅ Teacher approval logic
        if profile.role == "teacher":
            profile.approved = False   # require admin approval
        else:
            profile.approved = True    # students auto-approved

        profile.save()
        return user

    
# --- Login Form ---
class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })
    )


# --- Profile Form ---
from django import forms
from .models import Profile

from django import forms
from django.forms.widgets import ClearableFileInput
from .models import Profile

class ProfileForm(forms.ModelForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        })
    )

    class Meta:
        model = Profile
        fields = ['phone', 'bio', 'avatar', 'email']
        widgets = {
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your phone number'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Write a short bio about yourself'
            }),
            # ✅ Use ClearableFileInput instead of FileInput
            'avatar': ClearableFileInput(attrs={
                'class': 'form-control'
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['email'].initial = user.email  # prefill from User

    def save(self, commit=True, user=None):
        profile = super().save(commit=False)
        if user:
            user.email = self.cleaned_data['email']  # update User.email
            if commit:
                user.save()
                profile.save()
        return profile


class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username']   # ✅ only username
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter username'
            }),
        }

class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['role']   # ✅ only role
        widgets = {
            'role': forms.Select(attrs={'class': 'form-select'}),
        }


