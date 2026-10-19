from django.db import models

from plan_app.core.models import TimeStampedModel


class ExerciseType(TimeStampedModel):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(max_length=500, blank=True)
    tracks_metrics = models.BooleanField(default=True, help_text='Whether duration, distance and repetitions apply.')

    class Meta:
        db_table = 'exercise_types'
        ordering = ['name']

    def __str__(self):
        return self.name
