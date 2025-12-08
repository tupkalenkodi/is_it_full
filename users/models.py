from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        if not password:
            raise ValueError('The Password field must be set')

        email = self.normalize_email(email)
        user = self.model(email=email.lower(), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_verified', True)

        if not extra_fields.get('is_staff'):
            raise ValueError('Superuser must have is_staff=True.')
        if not extra_fields.get('is_superuser'):
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None  # Remove username field
    email = models.EmailField(unique=True, blank=False, null=False)

    # Foreign key to University model
    associated_university = models.ForeignKey(
        'universities.University',
        on_delete=models.CASCADE,
        related_name='users',
        null=True,
        blank=True
    )

    # Email verification
    is_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=100, blank=True, null=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []


    def __str__(self):
        return self.email

    def get_email_domain(self):
        """Extract domain from email (e.g., '@university.edu')"""
        if '@' in self.email:
            return '@' + self.email.split('@')[1]
        return None

    @staticmethod
    def get_university_from_email(email):
        """
        Get university from email domain.
        Returns University object or None if not found.
        """
        from universities.models import University

        if '@' not in email:
            return None

        email_domain = '@' + email.split('@')[1]

        try:
            return University.objects.get(email_domain=email_domain)
        except University.DoesNotExist:
            return None

    def save(self, *args, **kwargs):
        # Auto-detect university from email domain if not set
        if self.email and not self.associated_university:
            self.associated_university = self.get_university_from_email(self.email)

        super().save(*args, **kwargs)
