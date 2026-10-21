from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from plan_app.core.models import TimeStampedModel, validate_not_future


class Dog(TimeStampedModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dogs')
    name = models.CharField(_('name'), max_length=100)
    breed = models.CharField(_('breed'), max_length=100, default='Greyhound')
    date_of_birth = models.DateField(_('date of birth'), null=True, blank=True, validators=[validate_not_future])
    weight_kg = models.DecimalField(
        _('weight (kg)'), max_digits=6, decimal_places=3, null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.1')), MaxValueValidator(Decimal('150'))],
    )
    weekly_calorie_goal_kcal = models.PositiveIntegerField(
        _('weekly calorie goal (kcal)'), null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(100000)],
    )
    notes = models.TextField(_('notes'), max_length=1000, blank=True)

    class Meta:
        db_table = 'dogs'
        ordering = ['name']

    def __str__(self):
        return self.name


class WeightEntry(TimeStampedModel):
    dog = models.ForeignKey(Dog, on_delete=models.CASCADE, related_name='weights')
    date = models.DateField(_('date'), validators=[validate_not_future])
    weight_kg = models.DecimalField(
        _('weight (kg)'), max_digits=6, decimal_places=3,
        validators=[MinValueValidator(Decimal('0.1')), MaxValueValidator(Decimal('150'))],
    )
    notes = models.CharField(_('notes'), max_length=200, blank=True)

    class Meta:
        db_table = 'weight_entries'
        ordering = ['-date', '-id']
        verbose_name_plural = 'weight entries'
        constraints = [models.UniqueConstraint(fields=['dog', 'date'], name='unique_weight_entry_per_dog_date')]

    def __str__(self):
        return f'{self.dog} · {self.date} · {self.weight_kg} kg'
