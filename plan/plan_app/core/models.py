from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext, gettext_lazy as _

METRICS = ('duration_minutes', 'distance_km', 'repetitions')


def validate_not_future(value):
    if value > timezone.localdate():
        raise ValidationError(_('Date cannot be in the future.'))


def duration_field(verbose_name):
    return models.PositiveSmallIntegerField(
        verbose_name, null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(1440)]
    )


def distance_field(verbose_name):
    return models.DecimalField(
        verbose_name, max_digits=5, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.01')), MaxValueValidator(Decimal('200'))],
    )


def repetitions_field(verbose_name):
    return models.PositiveSmallIntegerField(
        verbose_name, null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(500)]
    )


def describe_activity(exercise_type, minutes=None, distance_km=None, repetitions=None):
    if exercise_type is None:
        return gettext('No plan')
    metrics = ' · '.join(filter(None, [
        distance_km and f'{distance_km.normalize():f} km',
        minutes and f'{minutes} min',
        repetitions and gettext('%(count)s reps') % {'count': repetitions},
    ]))
    return f'{exercise_type} — {metrics}' if metrics else str(exercise_type)


def reject_metrics(message, **metrics):
    for field, value in metrics.items():
        if value:
            raise ValidationError({field: message})


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
