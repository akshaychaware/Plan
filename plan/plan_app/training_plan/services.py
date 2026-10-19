from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q

from .models import PlannedActivity, TrainingPlan, TrainingPlanDay, Weekday

ACTIVITY_FIELDS = ('exercise_type', 'planned_duration_minutes', 'planned_distance_km', 'planned_repetitions', 'notes')


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


def ensure_days(plan):
    days = {day.day_of_week: day for day in plan.days.all()}
    for day_of_week in Weekday.values:
        if day_of_week not in days:
            days[day_of_week] = TrainingPlanDay.objects.create(training_plan=plan, day_of_week=day_of_week)
    return days


@transaction.atomic
def save_plan(plan):
    plan.full_clean()
    plan.save()
    ensure_days(plan)
    if plan.is_active:
        plan.dog.training_plans.exclude(pk=plan.pk).filter(is_active=True).update(is_active=False)
    return plan


@transaction.atomic
def activate_plan(plan):
    plan.is_active = True
    return save_plan(plan)


@transaction.atomic
def save_week(plan, week):
    """Upsert planned activities per day; `week` maps day_of_week to an ordered list of activity dicts."""
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
    return plan


@transaction.atomic
def start_new_plan(dog, *, name, start_date):
    current = active_plan(dog)
    if current and start_date <= current.start_date:
        raise ValidationError({'start_date': f'Must be after the current plan start ({current.start_date}).'})
    plan = save_plan(TrainingPlan(dog=dog, name=name, start_date=start_date, is_active=True))
    if current:
        current.end_date = start_date - timedelta(days=1)
        current.save(update_fields=['end_date', 'updated_at'])
        save_week(plan, {
            day.day_of_week: [{field: getattr(a, field) for field in ACTIVITY_FIELDS} for a in day.activities.all()]
            for day in current.days.prefetch_related('activities')
        })
    return plan
