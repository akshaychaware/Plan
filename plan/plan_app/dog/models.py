from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from plan_app.core.models import TimeStampedModel, validate_not_future


class Dog(TimeStampedModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dogs')
    name = models.CharField(max_length=100)
    breed = models.CharField(max_length=100, default='Greyhound')
    date_of_birth = models.DateField(null=True, blank=True, validators=[validate_not_future])
    weight_kg = models.DecimalField(
        'weight (kg)', max_digits=6, decimal_places=3, null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.1')), MaxValueValidator(Decimal('150'))],
    )
    notes = models.TextField(max_length=1000, blank=True)

    class Meta:
        db_table = 'dogs'
        ordering = ['name']

    def __str__(self):
        return self.name
