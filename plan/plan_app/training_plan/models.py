from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext, gettext_lazy as _

from plan_app.core.models import (
    TimeStampedModel, describe_activity, distance_field, duration_field, reject_metrics, repetitions_field,
)
from plan_app.dog.models import Dog
from plan_app.exercise.models import ExerciseType


class Weekday(models.IntegerChoices):
    MONDAY = 0, _('Monday')
    TUESDAY = 1, _('Tuesday')
    WEDNESDAY = 2, _('Wednesday')
    THURSDAY = 3, _('Thursday')
    FRIDAY = 4, _('Friday')
    SATURDAY = 5, _('Saturday')
    SUNDAY = 6, _('Sunday')


class TrainingPlan(TimeStampedModel):
    dog = models.ForeignKey(Dog, on_delete=models.CASCADE, related_name='training_plans')
    name = models.CharField(_('name'), max_length=100, default='Weekly plan')
    start_date = models.DateField(_('start date'))
    end_date = models.DateField(_('end date'), null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'training_plans'
        ordering = ['-is_active', '-start_date']
        indexes = [models.Index(fields=['dog', 'is_active'], name='training_plan_dog_active_idx')]

    def __str__(self):
        return f'{self.dog} · {self.name}'

    def clean(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError({'end_date': gettext('End date must be on or after the start date.')})


class TrainingPlanDay(models.Model):
    training_plan = models.ForeignKey(TrainingPlan, on_delete=models.CASCADE, related_name='days')
    day_of_week = models.PositiveSmallIntegerField(choices=Weekday.choices)

    class Meta:
        db_table = 'training_plan_days'
        ordering = ['day_of_week']
        constraints = [
            models.UniqueConstraint(fields=['training_plan', 'day_of_week'], name='unique_day_per_training_plan'),
        ]

    def __str__(self):
        return f'{self.training_plan} · {self.get_day_of_week_display()}'


class PlannedActivity(models.Model):
    training_plan_day = models.ForeignKey(TrainingPlanDay, on_delete=models.CASCADE, related_name='activities')
    exercise_type = models.ForeignKey(ExerciseType, on_delete=models.PROTECT, verbose_name=_('activity'))
    sequence = models.PositiveSmallIntegerField(default=0)
    planned_duration_minutes = duration_field(_('planned duration (min)'))
    planned_distance_km = distance_field(_('planned distance (km)'))
    planned_repetitions = repetitions_field(_('planned repetitions'))
    notes = models.CharField(_('notes'), max_length=200, blank=True)

    class Meta:
        db_table = 'planned_activities'
        ordering = ['sequence', 'id']
        verbose_name_plural = 'planned activities'

    def __str__(self):
        return self.summary

    @property
    def summary(self):
        return describe_activity(
            self.exercise_type, self.planned_duration_minutes, self.planned_distance_km, self.planned_repetitions
        )

    def clean(self):
        if self.exercise_type_id and not self.exercise_type.tracks_metrics:
            reject_metrics(
                gettext('%(activity)s does not track duration, distance or repetitions.')
                % {'activity': self.exercise_type},
                planned_duration_minutes=self.planned_duration_minutes,
                planned_distance_km=self.planned_distance_km,
                planned_repetitions=self.planned_repetitions,
            )
