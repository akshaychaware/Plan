from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext, gettext_lazy as _

from plan_app.core.models import (
    METRICS, TimeStampedModel, describe_activity, distance_field, duration_field, reject_metrics, repetitions_field,
)
from plan_app.dog.models import Dog
from plan_app.exercise.models import ExerciseType
from plan_app.training_plan.models import PlannedActivity


class TrainingSession(TimeStampedModel):
    class Status(models.TextChoices):
        COMPLETED = 'COMPLETED', _('Completed')
        PARTIALLY_COMPLETED = 'PARTIALLY_COMPLETED', _('Partially completed')
        SKIPPED = 'SKIPPED', _('Skipped')

    PLANNED = 'PLANNED'

    dog = models.ForeignKey(Dog, on_delete=models.CASCADE, related_name='sessions')
    planned_activity = models.ForeignKey(
        PlannedActivity, on_delete=models.SET_NULL, null=True, blank=True, related_name='sessions'
    )
    exercise_type = models.ForeignKey(ExerciseType, on_delete=models.PROTECT, verbose_name=_('activity'))
    date = models.DateField(_('date'))
    planned_exercise_type = models.ForeignKey(
        ExerciseType, on_delete=models.PROTECT, null=True, blank=True, related_name='+'
    )
    planned_duration_minutes = models.PositiveSmallIntegerField(null=True, blank=True)
    planned_distance_km = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    planned_repetitions = models.PositiveSmallIntegerField(null=True, blank=True)
    actual_duration_minutes = duration_field(_('actual duration (min)'))
    actual_distance_km = distance_field(_('actual distance (km)'))
    actual_repetitions = repetitions_field(_('actual repetitions'))
    status = models.CharField(_('status'), max_length=20, choices=Status.choices)
    calories_kcal = models.DecimalField(
        _('calories (kcal)'), max_digits=6, decimal_places=1, null=True, blank=True, editable=False
    )
    notes = models.TextField(_('notes'), max_length=1000, blank=True)

    class Meta:
        db_table = 'training_sessions'
        ordering = ['-date', 'id']
        indexes = [models.Index(fields=['dog', 'date'], name='training_session_dog_date_idx')]
        constraints = [
            models.UniqueConstraint(fields=['planned_activity', 'date'], name='unique_session_per_planned_activity'),
        ]

    def __str__(self):
        return f'{self.dog} · {self.date} · {self.exercise_type} · {self.get_status_display()}'

    @classmethod
    def from_planned(cls, dog, day, planned_activity=None):
        session = cls(dog=dog, date=day, planned_activity=planned_activity)
        if planned_activity:
            session.planned_exercise_type = session.exercise_type = planned_activity.exercise_type
            for metric in METRICS:
                value = getattr(planned_activity, f'planned_{metric}')
                setattr(session, f'planned_{metric}', value)
                setattr(session, f'actual_{metric}', value)
        return session

    @property
    def planned_summary(self):
        return describe_activity(
            self.planned_exercise_type, self.planned_duration_minutes, self.planned_distance_km,
            self.planned_repetitions,
        ) if self.planned_exercise_type_id else 'Unplanned'

    @property
    def actual_summary(self):
        return describe_activity(
            self.exercise_type, self.actual_duration_minutes, self.actual_distance_km, self.actual_repetitions
        )

    def clean(self):
        if self.date and self.date > timezone.localdate():
            raise ValidationError(gettext('Sessions cannot be recorded for future dates.'))
        if self.planned_activity_id:
            plan_day = self.planned_activity.training_plan_day
            if plan_day.training_plan.dog_id != self.dog_id or (
                self.date and plan_day.day_of_week != self.date.weekday()
            ):
                raise ValidationError(
                    gettext('This planned activity is not in %(dog)s’s plan for this date.') % {'dog': self.dog}
                )
        actual = {f'actual_{metric}': getattr(self, f'actual_{metric}') for metric in METRICS}
        if self.status == self.Status.SKIPPED:
            reject_metrics(gettext('Leave empty for skipped sessions.'), **actual)
        if self.exercise_type_id and not self.exercise_type.tracks_metrics:
            reject_metrics(
                gettext('%(activity)s does not track duration, distance or repetitions.')
                % {'activity': self.exercise_type}, **actual
            )
