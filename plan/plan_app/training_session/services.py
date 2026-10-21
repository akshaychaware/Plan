from datetime import timedelta

from django.db import transaction

from plan_app.core.models import METRICS
from plan_app.training_plan.services import planned_activities_for

from .models import TrainingSession

Status = TrainingSession.Status


def status_label(status):
    return Status(status).label if status in Status.values else 'Planned'


def day_entries(dog, day, sessions=None):
    """Planned activities for `day` paired with their recorded sessions, plus any unplanned sessions."""
    if sessions is None:
        sessions = list(dog.sessions.select_related('exercise_type', 'planned_exercise_type').filter(date=day))
    by_planned = {s.planned_activity_id: s for s in sessions if s.planned_activity_id}
    activities = []
    for planned in planned_activities_for(dog, day):
        session = by_planned.pop(planned.pk, None)
        activities.append({'planned': planned, 'session': session})
    activities += [
        {'planned': None, 'session': s} for s in sessions if not s.planned_activity_id or s.planned_activity_id in by_planned
    ]
    for activity in activities:
        activity['exercise'] = (activity['planned'] or activity['session']).exercise_type
        activity['status'] = activity['session'].status if activity['session'] else TrainingSession.PLANNED
        activity['status_label'] = status_label(activity['status'])
    return {'date': day, 'activities': activities}


def overview(dog, start, end):
    days = [start + timedelta(days=offset) for offset in range((end - start).days + 1)]
    sessions = list(
        dog.sessions.select_related('exercise_type', 'planned_exercise_type').filter(date__range=(start, end))
    )
    return [day_entries(dog, d, [s for s in sessions if s.date == d]) for d in days]


def week_overview(dog, day):
    monday = day - timedelta(days=day.weekday())
    return overview(dog, monday, monday + timedelta(days=6))


def month_overview(dog, day):
    first = day.replace(day=1)
    return overview(dog, first, (first + timedelta(days=32)).replace(day=1) - timedelta(days=1))


def history_days(sessions, dates):
    """One entry per date with its sessions and their combined calories (None when no session has calories)."""
    by_date = {day: [] for day in dates}
    for session in sessions.filter(date__in=list(by_date)):
        by_date[session.date].append(session)
    days = []
    for day, day_sessions in by_date.items():
        calories = [s.calories_kcal for s in day_sessions if s.calories_kcal is not None]
        days.append({'date': day, 'sessions': day_sessions, 'calories_kcal': sum(calories) if calories else None})
    return days


@transaction.atomic
def save_session(session, **values):
    for field, value in values.items():
        setattr(session, field, value)
    if session.status == Status.SKIPPED:
        for metric in METRICS:
            if f'actual_{metric}' not in values:
                setattr(session, f'actual_{metric}', None)
    session.full_clean()
    session.save()
    return session


def record_session(*, dog, day, planned_activity=None, **values):
    existing = planned_activity and dog.sessions.filter(date=day, planned_activity=planned_activity).first()
    return save_session(existing or TrainingSession.from_planned(dog, day, planned_activity), **values)


def complete_as_planned(dog, planned_activity, day):
    if dog.sessions.filter(date=day, planned_activity=planned_activity).exists():
        return None
    return record_session(dog=dog, day=day, planned_activity=planned_activity, status=Status.COMPLETED)
