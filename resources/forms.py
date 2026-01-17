from django import forms
from .models import Note
from .models import StudentResource

class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ['title', 'topic', 'version', 'file']

    def clean_file(self):
        f = self.cleaned_data.get('file')
        if not f:
            raise forms.ValidationError("Please upload a PDF file.")
        if not f.name.lower().endswith('.pdf'):
            raise forms.ValidationError("Only PDF files are allowed.")
        return f

class StudentResourceForm(forms.ModelForm):
    class Meta:
        model = StudentResource
        fields = ['title', 'description', 'file']
from django import forms
from .models import Note, StudentResource, Rating, Recommendation

class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ['title', 'topic', 'version', 'file']

    def clean_file(self):
        f = self.cleaned_data.get('file')
        if not f:
            raise forms.ValidationError("Please upload a PDF file.")
        if not f.name.lower().endswith('.pdf'):
            raise forms.ValidationError("Only PDF files are allowed.")
        return f


class StudentResourceForm(forms.ModelForm):
    class Meta:
        model = StudentResource
        fields = ['title', 'description', 'file']


# --- Ratings ---

class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['value']
        widgets = {
            'value': forms.RadioSelect(
                choices=[(i, '★' * i) for i in range(1, 6)]  # show stars instead of numbers
            )
        }


# --- Recommendations ---
class RecommendationForm(forms.ModelForm):
    class Meta:
        model = Recommendation
        fields = ['comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Why do you recommend this?'})
        }
