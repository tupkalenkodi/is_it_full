from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()


class SignupForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label="University Email",
        widget=forms.EmailInput(attrs={
            'placeholder': 'name@associated_university.edu',
            'autocomplete': 'email',
            'class': 'form-control'
        })
    )

    password1 = forms.CharField(
        required=True,
        label='Password',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Enter your password',
            'autocomplete': 'new-password',
            'class': 'form-control'
        })
    )

    password2 = forms.CharField(
        required=True,
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Confirm your password',
            'autocomplete': 'new-password',
            'class': 'form-control'
        })
    )

    class Meta:
        model = User
        fields = ('email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')

        # CHECK IF USER ALREADY EXISTS
        if User.objects.filter(email=email).exists():
            raise ValidationError("An account with this email already exists.")

        # NORMALIZE EMAIL TO LOWERCASE
        email = email.lower()

        # EXTRACT DOMAIN AND CHECK IF UNIVERSITY EXISTS
        if '@' not in email:
            raise ValidationError("Please enter a valid email address.")

        email_domain = '@' + email.split('@')[1]

        from universities.models import University

        # CHECK IF AN APPROVED UNIVERSITY EXISTS WITH THIS DOMAIN
        if not University.objects.filter(email_domain=email_domain, is_approved=True).exists():

            raise ValidationError(
                "This associated_university is not yet supported."
            )

        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        # mvp
        user.is_active = True

        if commit:
            user.save()

        return user


class SigninForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={
            'placeholder': 'Enter your email address',
            'autocomplete': 'email',
            'class': 'form-control'
        }),
    )

    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password',
            'class': 'form-control'
        })
    )

# (disabled for MVP)
# class CustomPasswordChangeForm(PasswordChangeForm):
#     old_password = forms.CharField(
#         label='Current Password',
#         widget=forms.PasswordInput(attrs={
#             'placeholder': 'Enter your current password',
#             'autocomplete': 'current-password',
#             'class': 'form-control'
#         })
#     )
#
#     new_password1 = forms.CharField(
#         label='New Password',
#         widget=forms.PasswordInput(attrs={
#             'placeholder': 'Enter your new password',
#             'autocomplete': 'new-password',
#             'class': 'form-control'
#         })
#     )
#
#     new_password2 = forms.CharField(
#         label='Confirm New Password',
#         widget=forms.PasswordInput(attrs={
#             'placeholder': 'Confirm your new password',
#             'autocomplete': 'new-password',
#             'class': 'form-control'
#         })
#     )