from django import forms
from .models import Note, StudentResource, Rating, Recommendation, CATEGORY_CHOICES

# --- Notes ---
class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ['title', 'topic', 'version', 'file', 'category']  # ✅ added category
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter note title'
            }),
            'topic': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter topic'
            }),
            'version': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Version number'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }, choices=[('', 'Optional: Select a category')] + CATEGORY_CHOICES),
        }

    def clean_file(self):
        f = self.cleaned_data.get('file')
        if not f:
            raise forms.ValidationError("Please upload a PDF file.")
        if not f.name.lower().endswith('.pdf'):
            raise forms.ValidationError("Only PDF files are allowed.")
        return f


# --- Student Resources ---
class StudentResourceForm(forms.ModelForm):
    class Meta:
        model = StudentResource
        fields = ['title', 'description', 'file', 'category']  # ✅ added category
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter resource title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Add a short description'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }, choices=[('', 'Optional: Select a category')] + CATEGORY_CHOICES),
        }


# --- Ratings ---
class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['value']
        widgets = {
            'value': forms.RadioSelect(
                choices=[(i, '★' * i) for i in range(1, 6)],
                attrs={'class': 'form-check-input'}
            )
        }


# --- Recommendations ---
class RecommendationForm(forms.ModelForm):
    class Meta:
        model = Recommendation
        fields = ['comment']
        widgets = {
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Why do you recommend this?'
            })
        }
