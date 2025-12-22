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


class User(AbstractBaseUser, PermissionsMixin):
    """
    Single unified user model that handles both regular university users
    and system administrators through Django's built-in permission system.
    """

    # Authentication fields
    username = None
    email = models.EmailField(unique=True, blank=False, null=False)

    # Permission fields (from PermissionsMixin)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    # is_superuser comes from PermissionsMixin

    # University association (nullable for system admins)
    associated_university = models.ForeignKey(
        'universities.University',
        on_delete=models.CASCADE,
        related_name='users',
        null=True,
        blank=True,
    )

    # Optional: Reputation system for community incentives
    reputation_score = models.IntegerField(
        default=0,
    )

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'users_user'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['associated_university']),
        ]

    def __str__(self):
        return self.email

    def clean(self):
        """
        Validate and auto-assign university based on email domain.
        System admins (is_superuser=True) don't need a university.
        """
        # Superusers don't need a university
        if self.is_superuser:
            self.associated_university = None
            return

        # Regular users must have a university
        if self.email and not self.associated_university:
            university = self.get_university_from_email(self.email)
            if university:
                self.associated_university = university
            else:
                raise ValidationError({
                    'email': f'No approved university found for email domain: {self.get_email_domain()}'
                })

    def save(self, *args, **kwargs):
        """Override save to run validation."""
        # Only run clean() for new users or if email/university changed
        if not self.pk or self.email != self.__class__.objects.filter(pk=self.pk).values_list('email',
                                                                                              flat=True).first():
            self.clean()
        super().save(*args, **kwargs)

    # Properties to check user type
    @property
    def is_university_user(self):
        """Check if this is a regular university user."""
        return self.associated_university is not None and not self.is_superuser

    @property
    def is_system_admin(self):
        """Check if this is a system administrator."""
        return self.is_superuser and self.is_staff

    # Permission methods
    def can_manage_space(self, space):
        """Check if user can create/update/delete a space."""
        if not self.is_active:
            return False

        # System admins can manage any space
        if self.is_system_admin:
            return True

        # University users can only manage spaces in their university
        return (
                self.is_university_user and
                space.university == self.associated_university
        )

    def can_report_occupancy(self, space):
        """Check if user can report occupancy for a space."""
        if not self.is_active:
            return False

        # Only university users can report (not system admins)
        return (
                self.is_university_user and
                space.university == self.associated_university
        )

    def approve_university(self, university):
        """System admin method to approve a university."""
        if self.is_system_admin:
            university.is_approved = True
            university.save(update_fields=['is_approved'])
            return True
        return False

    # Utility methods
    def get_email_domain(self):
        """Extract domain from email (e.g., '@student.upr.si')."""
        if '@' in self.email:
            return '@' + self.email.split('@')[1]
        return None

    @staticmethod
    def get_university_from_email(email):
        """Get university object from email domain."""
        from universities.models import University

        if '@' not in email:
            return None

        email_domain = '@' + email.split('@')[1]

        try:
            # Only return approved universities
            return University.objects.get(
                email_domain=email_domain,
                is_approved=True
            )
        except University.DoesNotExist:
            return None
