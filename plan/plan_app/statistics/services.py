from datetime import timedelta

from django.db.models import Avg, Count, F, Q, Sum
from django.utils import timezone

from plan_app.training_session.models import TrainingSession

Status = TrainingSession.Status
PERIODS = {'week': 'This week', 'month': 'This month', 'all': 'All time'}


def period_start(period, today):
    if period == 'week':
        return today - timedelta(days=today.weekday())
    if period == 'month':
        return today.replace(day=1)
    return None


def current_streak(dog, today):
    dates = (
        dog.sessions.exclude(status=Status.SKIPPED)
        .filter(date__lte=today)
        .order_by('-date')
        .values_list('date', flat=True)
        .distinct()
    )
    streak, expected = 0, today
    for day in dates:
        if streak == 0 and day == today - timedelta(days=1):
            expected = day
        if day != expected:
            break
        streak += 1
        expected -= timedelta(days=1)
    return streak


def summarize(dog, period='all', today=None):
    today = today or timezone.localdate()
    start = period_start(period, today)
    sessions = dog.sessions.filter(date__lte=today)
    if start:
        sessions = sessions.filter(date__gte=start)

    stats = sessions.aggregate(
        total=Count('id'),
        completed=Count('id', filter=Q(status=Status.COMPLETED)),
        partially_completed=Count('id', filter=Q(status=Status.PARTIALLY_COMPLETED)),
        skipped=Count('id', filter=Q(status=Status.SKIPPED)),
        total_minutes=Sum('actual_duration_minutes'),
        total_distance_km=Sum('actual_distance_km'),
    )
    distinct_days = sessions.order_by().values('date').distinct()
    by_exercise = list(
        sessions.exclude(status=Status.SKIPPED)
        .values(exercise=F('exercise_type__name'))
        .annotate(
            sessions=Count('id'),
            total_minutes=Sum('actual_duration_minutes'),
            average_minutes=Avg('actual_duration_minutes'),
            total_distance_km=Sum('actual_distance_km'),
        )
        .order_by('-sessions', 'exercise')
    )
    trained = stats['total'] - stats['skipped']
    for row in by_exercise:
        row['share'] = round(100 * row['sessions'] / trained)
    stats.update(
        period=period,
        start_date=start,
        end_date=today,
        training_days=distinct_days.filter(exercise_type__tracks_metrics=True).count(),
        rest_days=distinct_days.filter(exercise_type__tracks_metrics=False).exclude(status=Status.SKIPPED).count(),
        completion_rate=round(100 * stats['completed'] / stats['total']) if stats['total'] else 0,
        streak=current_streak(dog, today),
        by_exercise=by_exercise,
    )
    return stats


def week_progress(week):
    training = [
        a for entry in week for a in entry['activities']
        if a['planned'] and a['planned'].exercise_type.tracks_metrics
    ]
    done = sum(1 for a in training if a['session'] and a['session'].status != Status.SKIPPED)
    return {
        'done': done,
        'target': len(training),
        'percent': round(100 * done / len(training)) if training else 0,
    }
