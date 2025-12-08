from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        if not password:
            raise ValueError('The Password field must be set')

        extra_fields.setdefault('is_active', False)
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)

        email = self.normalize_email(email)
        user = self.model(email=email.lower(), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if not extra_fields.get('is_staff'):
            raise ValueError('Superuser must have is_staff=True.')
        if not extra_fields.get('is_superuser'):
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True, blank=False, null=False)

    # FOREIGN KEY TO UNIVERSITY MODEL
    associated_university = models.ForeignKey(
        'universities.University',
        on_delete=models.CASCADE,
        related_name='users',
        null=True,
        blank=True
    )

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []


    def __str__(self):
        return self.email

    def get_email_domain(self):
        # EXTRACT DOMAIN FROM EMAIL (e.g. '@student.upr.si')
        if '@' in self.email:
            return '@' + self.email.split('@')[1]
        return None

    # GET UNIVERSITY FROM EMAIL DOMAIN
    # RETURNS UNIVERSITY OBJECT OR NONE IF NOT FOUND
    @staticmethod
    def get_university_from_email(email):
        from universities.models import University

        if '@' not in email:
            return None

        email_domain = '@' + email.split('@')[1]

        try:
            return University.objects.get(email_domain=email_domain)
        except University.DoesNotExist:
            return None

    def save(self, *args, **kwargs):
        # AUTO-DETECT UNIVERSITY FROM EMAIL DOMAIN IF NOT SET
        if self.email and not self.associated_university:
            university = self.get_university_from_email(self.email)
            if university:
                self.associated_university = university
            else:
                raise ValueError("Cannot save user without a valid university")

        super().save(*args, **kwargs)
