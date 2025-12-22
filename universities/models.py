from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError


class University(models.Model):
    name = models.CharField(max_length=200, unique=True)
    email_domain = models.CharField(
        max_length=100,
        unique=True,
    )
    # TODO: enable associated_university validation by admin
    is_approved = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def clean(self):
        if self.email_domain and not self.email_domain.startswith('@'):
            self.email_domain = '@' + self.email_domain

        if self.email_domain and self.email_domain.count('@') != 1:
            raise ValidationError({'email_domain': 'Invalid email domain format'})

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class Space(models.Model):
    SPACE_TYPE_STUDYING = 'studying'
    SPACE_TYPE_EATING = 'eating'
    SPACE_TYPE_COFFEE = 'coffee'

    SPACE_TYPES = [
        (SPACE_TYPE_STUDYING, 'Studying'),
        (SPACE_TYPE_EATING, 'Eating'),
        (SPACE_TYPE_COFFEE, 'Coffee'),
    ]

    PRICE_RANGE_CHOICES = [
        (1, '$'),
        (2, '$$'),
        (3, '$$$'),
    ]

    # CORE FIELDS (ALL SPACES)
    name = models.CharField(max_length=200)
    location = models.CharField(
        max_length=200,
    )

    space_type = models.CharField(
        max_length=20,
        choices=SPACE_TYPES
    )

    # Occupancy tracking
    current_occupancy = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )

    # Composite relationship with University
    associated_university = models.ForeignKey(
        University,
        on_delete=models.CASCADE,
    )

    # Composite pattern: parent-child relationship
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
    )

    # Assocation relationship with University
    last_updated_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
    )

    last_updated = models.DateTimeField(null=True, blank=True)

    # TYPE-SPECIFIC FIELDS (NULLABLE FOR OTHER TYPES)

    # Studying spaces
    has_plugs = models.BooleanField(null=True, blank=True)
    has_wifi = models.BooleanField(null=True, blank=True)

    # Eating spaces
    has_student_discounts = models.BooleanField(null=True, blank=True)
    eating_price_range = models.IntegerField(
        null=True,
        blank=True,
        choices=PRICE_RANGE_CHOICES
    )

    # Coffee spaces
    coffee_quality = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    coffee_price_range = models.IntegerField(
        null=True,
        blank=True,
        choices=PRICE_RANGE_CHOICES
    )


    class Meta:
        ordering = ['associated_university', 'space_type', 'name']
        unique_together = [['associated_university', 'name', 'location']]
        indexes = [
            models.Index(fields=['associated_university', 'space_type']),
            models.Index(fields=['parent']),
        ]

    def __str__(self):
        return f"{self.name} ({self.location}) - {self.associated_university.name}"

    def get_full_name(self):
        if self.parent:
            return f"{self.parent.get_full_name()} > {self.name}"
        return self.name

    def get_occupancy(self):
        # If this space has its own occupancy, return it
        if self.current_occupancy is not None:
            return self.current_occupancy

        # If composite, calculate average from children
        children = self.children.all()
        if children.exists():
            occupancies = [
                child.get_occupancy()
                for child in children
            ]
            # Filter out None values
            valid_occupancies = [occ for occ in occupancies if occ is not None]

            if valid_occupancies:
                return sum(valid_occupancies) / len(valid_occupancies)

        return None

    def is_composite(self):
        return self.children.exists()

    def get_all_descendants(self):
        descendants = []
        for child in self.children.all():
            descendants.append(child)
            descendants.extend(child.get_all_descendants())
        return descendants

    def clean(self):
        # Prevent circular parent relationships
        if self.parent:
            if self.parent == self:
                raise ValidationError("A space cannot be its own parent")

            # Check for circular reference
            current = self.parent
            while current:
                if current == self:
                    raise ValidationError("Circular parent relationship detected")
                current = current.parent

        # Validate type-specific fields
        if self.space_type == self.SPACE_TYPE_STUDYING:
            if self.has_plugs is None:
                self.has_plugs = False
            if self.has_wifi is None:
                self.has_wifi = False

        elif self.space_type == self.SPACE_TYPE_EATING:
            if self.has_student_discounts is None:
                self.student_discounts = False
            if self.eating_price_range is None:
                self.eating_price_range = 2

        elif self.space_type == self.SPACE_TYPE_COFFEE:
            if self.coffee_quality is None:
                self.coffee_quality = 3
            if self.coffee_price_range is None:
                self.coffee_price_range = 2

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
