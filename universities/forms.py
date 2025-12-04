from django import forms
from .models import University


class UniversityForm(forms.ModelForm):
    class Meta:
        model = University
        fields = ['name', 'email_domain', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'University Name'
            }),
            'email_domain': forms.TextInput(attrs={
                'placeholder': '@university.edu'
            }),
        }