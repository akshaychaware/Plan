from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone, translation
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


class AuditEntry(models.Model):
    """Who created or changed a training plan or history entry, when, and the old → new values."""

    class Target(models.TextChoices):
        PLAN = 'PLAN', 'Training plan'
        SESSION = 'SESSION', 'History entry'

    class Action(models.TextChoices):
        CREATED = 'CREATED', 'Created'
        UPDATED = 'UPDATED', 'Updated'

    dog = models.ForeignKey('plan_app.Dog', on_delete=models.CASCADE, related_name='audit_entries')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    username = models.CharField(max_length=150, blank=True)
    target = models.CharField(max_length=10, choices=Target.choices)
    object_id = models.PositiveBigIntegerField()
    object_repr = models.CharField(max_length=200)
    action = models.CharField(max_length=10, choices=Action.choices)
    changes = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_entries'
        ordering = ['-created_at', '-id']
        verbose_name_plural = 'audit entries'
        indexes = [models.Index(fields=['dog', 'created_at'], name='audit_entry_dog_created_idx')]

    def __str__(self):
        return f'{self.created_at:%Y-%m-%d %H:%M} · {self.username or "-"} · {self.object_repr}'

    @staticmethod
    def snapshot(obj, fields):
        """Untranslated, readable values of `fields` keyed by verbose name, so entries read the same in every language."""
        values = {}
        with translation.override(None):
            for name in fields:
                value = getattr(obj, name)
                if obj._meta.get_field(name).choices and value:
                    value = getattr(obj, f'get_{name}_display')()
                values[str(obj._meta.get_field(name).verbose_name)] = '' if value in (None, '') else str(value)
        return values

    @classmethod
    def stored(cls, obj, fields):
        """Snapshot of `obj` as currently saved, or None when it has not been saved yet."""
        previous = obj.pk and type(obj).objects.filter(pk=obj.pk).first()
        return cls.snapshot(previous, fields) if previous else None

    @classmethod
    def log(cls, user, target, obj, before, after):
        """Save the differences between two snapshots (`before=None` = just created); nothing changed = no entry."""
        if before is None:
            action, changes = cls.Action.CREATED, [{'field': f, 'old': '', 'new': v} for f, v in after.items() if v]
        else:
            action = cls.Action.UPDATED
            changes = [{'field': f, 'old': before.get(f, ''), 'new': v} for f, v in after.items() if before.get(f, '') != v]
            if not changes:
                return None
        known = user if user is not None and user.is_authenticated else None
        with translation.override(None):
            label = str(obj)[:200]
        return cls.objects.create(
            dog_id=obj.dog_id, user=known, username=known.get_username() if known else '', target=target,
            object_id=obj.pk, object_repr=label, action=action, changes=changes,
        )
