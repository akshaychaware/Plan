from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import translation
from django.utils.formats import date_format
from django.utils.translation import gettext

from plan_app.core.models import AuditEntry

from .models import PlannedActivity, TrainingPlan, TrainingPlanDay, Weekday

ACTIVITY_FIELDS = ('exercise_type', 'planned_duration_minutes', 'planned_distance_km', 'planned_repetitions', 'notes')
PLAN_FIELDS = ('name', 'start_date', 'end_date', 'is_active')


def active_plan(dog):
    return dog.training_plans.filter(is_active=True).first()


def plan_for_date(dog, day):
    return (
        dog.training_plans.filter(start_date__lte=day)
        .filter(Q(end_date__isnull=True) | Q(end_date__gte=day))
        .order_by('-is_active', '-start_date')
        .first()
    )


def planned_activities_for(dog, day):
    plan = plan_for_date(dog, day)
    if plan is None:
        return PlannedActivity.objects.none()
    return PlannedActivity.objects.select_related('exercise_type').filter(
        training_plan_day__training_plan=plan, training_plan_day__day_of_week=day.weekday()
    )


def planned_activities_by_date(dog, days):
    """`planned_activities_for` for every date in `days` using two queries instead of two per date."""
    if not days:
        return {}
    plans = list(
        dog.training_plans.filter(start_date__lte=max(days))
        .filter(Q(end_date__isnull=True) | Q(end_date__gte=min(days)))
        .order_by('-is_active', '-start_date')
    )
    by_plan_day = {}
    for activity in PlannedActivity.objects.select_related('exercise_type', 'training_plan_day').filter(
        training_plan_day__training_plan__in=plans
    ):
        key = (activity.training_plan_day.training_plan_id, activity.training_plan_day.day_of_week)
        by_plan_day.setdefault(key, []).append(activity)
    result = {}
    for day in days:
        plan = next((p for p in plans if p.start_date <= day and (p.end_date is None or p.end_date >= day)), None)
        result[day] = by_plan_day.get((plan.pk, day.weekday()), []) if plan else []
    return result


def ensure_days(plan):
    days = {day.day_of_week: day for day in plan.days.all()}
    for day_of_week in Weekday.values:
        if day_of_week not in days:
            days[day_of_week] = TrainingPlanDay.objects.create(training_plan=plan, day_of_week=day_of_week)
    return days


def week_snapshot(plan):
    """Each weekday's planned activities as one readable line, for the audit log."""
    days = {day.day_of_week: day for day in plan.days.prefetch_related('activities__exercise_type')}
    with translation.override(None):
        return {
            str(label): '; '.join(
                f'{a.summary} ({a.notes})' if a.notes else a.summary for a in days[value].activities.all()
            ) if value in days else ''
            for value, label in Weekday.choices
        }


@transaction.atomic
def save_plan(plan, user=None):
    before = AuditEntry.stored(plan, PLAN_FIELDS)
    plan.full_clean()
    plan.save()
    AuditEntry.log(user, AuditEntry.Target.PLAN, plan, before, AuditEntry.snapshot(plan, PLAN_FIELDS))
    ensure_days(plan)
    if plan.is_active:
        plan.dog.training_plans.exclude(pk=plan.pk).filter(is_active=True).update(is_active=False)
    return plan


@transaction.atomic
def activate_plan(plan, user=None):
    plan.is_active = True
    return save_plan(plan, user)


@transaction.atomic
def save_week(plan, week, user=None):
    """Upsert planned activities per day; `week` maps day_of_week to an ordered list of activity dicts."""
    before = week_snapshot(plan)
    days = ensure_days(plan)
    for day_of_week, items in week.items():
        day = days[day_of_week]
        existing = {activity.pk: activity for activity in day.activities.all()}
        kept = []
        for sequence, item in enumerate(items):
            activity = existing.get(item.get('id')) or PlannedActivity(training_plan_day=day)
            for field in ACTIVITY_FIELDS:
                setattr(activity, field, item.get(field, '' if field == 'notes' else None))
            activity.sequence = sequence
            activity.full_clean()
            activity.save()
            kept.append(activity.pk)
        day.activities.exclude(pk__in=kept).delete()
    AuditEntry.log(user, AuditEntry.Target.PLAN, plan, before, week_snapshot(plan))
    return plan


@transaction.atomic
def start_new_plan(dog, *, name, start_date, user=None):
    current = active_plan(dog)
    if current and start_date <= current.start_date:
        raise ValidationError({'start_date': gettext('Must be after the current plan start (%(date)s).') % {
            'date': date_format(current.start_date, 'j M Y'),
        }})
    before = current and AuditEntry.snapshot(current, PLAN_FIELDS)
    plan = save_plan(TrainingPlan(dog=dog, name=name, start_date=start_date, is_active=True), user)
    if current:
        current.end_date = start_date - timedelta(days=1)
        current.save(update_fields=['end_date', 'updated_at'])
        AuditEntry.log(user, AuditEntry.Target.PLAN, current, before, AuditEntry.stored(current, PLAN_FIELDS))
        save_week(plan, {
            day.day_of_week: [{field: getattr(a, field) for field in ACTIVITY_FIELDS} for a in day.activities.all()]
            for day in current.days.prefetch_related('activities')
        }, user)
    return plan
