from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext, gettext_noop

from plan_app.core.models import TimeStampedModel

BUILT_IN_NAMES = [
    gettext_noop('Bike/Cycle'), gettext_noop('Hill Climbing'), gettext_noop('Rest'), gettext_noop('Running'),
    gettext_noop('Swimming'), gettext_noop('Walking'),
]


class ExerciseType(TimeStampedModel):
    class CaloriesBasis(models.TextChoices):
        SESSION = 'SESSION', 'Per session'
        DISTANCE = 'DISTANCE', 'Per distance (km)'
        DURATION = 'DURATION', 'Per duration (min)'

    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(max_length=500, blank=True)
    tracks_metrics = models.BooleanField(default=True, help_text='Whether duration, distance and repetitions apply.')
    average_calories_kcal = models.DecimalField(
        'average calories (kcal)', max_digits=6, decimal_places=1, null=True, blank=True,
        validators=[MinValueValidator(Decimal('0'))],
    )
    calories_basis = models.CharField(max_length=10, choices=CaloriesBasis.choices, default=CaloriesBasis.SESSION)
    calories_basis_amount = models.DecimalField(
        'calories basis amount', max_digits=6, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text='The km or minutes the average calories refer to, e.g. 2 for "50 kcal per 2 km".',
    )

    class Meta:
        db_table = 'exercise_types'
        ordering = ['name']

    def __str__(self):
        return gettext(self.name)

    def clean(self):
        if self.calories_basis != self.CaloriesBasis.SESSION and not self.calories_basis_amount:
            raise ValidationError({'calories_basis_amount': 'Required for distance or duration based calories.'})

    def calories_for(self, duration_minutes=None, distance_km=None):
        """kcal for one session; scaled by the actual distance or duration, which count as 0 when not recorded."""
        if self.average_calories_kcal is None or (
            self.calories_basis != self.CaloriesBasis.SESSION and not self.calories_basis_amount
        ):
            return None
        if self.calories_basis == self.CaloriesBasis.SESSION:
            return self.average_calories_kcal
        actual = distance_km if self.calories_basis == self.CaloriesBasis.DISTANCE else duration_minutes
        kcal = self.average_calories_kcal * Decimal(actual or 0) / self.calories_basis_amount
        return kcal.quantize(Decimal('0.1'))
