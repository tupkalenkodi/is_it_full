from django import forms
from .models import University, Space


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

class OccupancyUpdateForm(forms.ModelForm):
    class Meta:
        model = Space
        fields = ['current_occupancy']


class SpaceCreationForm(forms.ModelForm):
    class Meta:
        model = Space
        fields = ['name', 'location', 'space_type', 'parent', 'has_plugs', 'has_wifi']

    def __init__(self, *args, **kwargs):
        university = kwargs.pop('university', None)
        super().__init__(*args, **kwargs)
        if university:
            # Ensure they can only select parent spaces from their own university
            self.fields['parent'].queryset = Space.objects.filter(associated_university=university)
