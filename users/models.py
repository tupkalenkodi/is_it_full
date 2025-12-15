from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.exceptions import ValidationError
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


class BaseUser(AbstractBaseUser, PermissionsMixin):
    class Meta:
        abstract = True

    username = None
    email = models.EmailField(unique=True, blank=False, null=False)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email


class User(BaseUser):
    class Meta:
        db_table = 'users_user'


class UniversityUser(User):
    associated_university = models.ForeignKey(
        'universities.University',
        on_delete=models.CASCADE,
        related_name='university_users',
        null=False,
        blank=False
    )

    def clean(self):
        # Auto-detect university from email if not set
        if self.email and not self.associated_university:
            university = self.get_university_from_email(self.email)
            if university:
                self.associated_university = university
            else:
                raise ValidationError({
                    'email': f'No university found for email domain: {self.email}'
                })

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def can_manage_space(self, space):
        return (
                self.is_active and
                space.university == self.associated_university
        )

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


class SystemAdmin(User):
    def save(self, *args, **kwargs):
        self.is_staff = True
        self.is_superuser = True
        self.is_active = True
        super().save(*args, **kwargs)

    def approve_university(self, university):
        if self.is_superuser and self.is_active:
            university.is_approved = True
            university.save(update_fields=['is_approved'])
            return True
        return False
