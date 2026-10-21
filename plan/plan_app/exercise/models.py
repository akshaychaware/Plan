from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from plan_app.core.models import TimeStampedModel


class ExerciseType(TimeStampedModel):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(max_length=500, blank=True)
    tracks_metrics = models.BooleanField(default=True, help_text='Whether duration, distance and repetitions apply.')
    average_calories_kcal = models.DecimalField(
        'average calories (kcal)', max_digits=6, decimal_places=1, null=True, blank=True,
        validators=[MinValueValidator(Decimal('0'))],
    )

    class Meta:
        db_table = 'exercise_types'
        ordering = ['name']

    def __str__(self):
        return self.name
