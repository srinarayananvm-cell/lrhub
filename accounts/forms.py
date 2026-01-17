from django import forms
from .models import Profile
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm


# --- Signup Form ---
class SignupForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    role = forms.ChoiceField(
        choices=Profile.ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Role"
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'role']   # ✅ includes role
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

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
        # ✅ Avoid duplicate profile
        profile, created = Profile.objects.get_or_create(user=user)
        profile.role = self.cleaned_data["role"]   # teacher or student
        profile.save()
        return user


# --- Login Form ---
class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )


# --- Profile Form ---
class ProfileForm(forms.ModelForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Profile
        fields = ['phone', 'bio', 'avatar', 'email']

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



