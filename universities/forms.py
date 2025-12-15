from django import forms
from .models import University


class UniversityForm(forms.ModelForm):
    class Meta:
        model = University
        fields = ['name', 'email_domain', 'is_approved']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'University Name'
            }),
            'email_domain': forms.TextInput(attrs={
                'placeholder': '@associated_university.edu'
            }),
            'is_approved': forms.CheckboxInput()
        }