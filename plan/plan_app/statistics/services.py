from datetime import timedelta

from django.db.models import Avg, Count, F, Q, Sum
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from plan_app.training_session.models import TrainingSession

Status = TrainingSession.Status
PERIODS = {'week': _('This week'), 'month': _('This month'), 'all': _('All time')}


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


def longest_streak(dates):
    """Longest run of consecutive days in sorted, distinct `dates` as {'days', 'start', 'end'}, or None."""
    best, start, previous = None, None, None
    for day in dates:
        if previous is None or day - previous != timedelta(days=1):
            start = day
        days = (day - start).days + 1
        if best is None or days > best['days']:
            best = {'days': days, 'start': start, 'end': day}
        previous = day
    return best


def personal_records(dog, today):
    done = dog.sessions.exclude(status=Status.SKIPPED).filter(date__lte=today)
    longest = (
        done.filter(actual_distance_km__gt=0).select_related('exercise_type')
        .order_by('-actual_distance_km', 'date').first()
    )
    weekly = {}
    for day, kcal in done.filter(calories_kcal__gt=0).order_by('date').values_list('date', 'calories_kcal'):
        monday = day - timedelta(days=day.weekday())
        weekly[monday] = weekly.get(monday, 0) + kcal
    best_week = max(weekly.items(), key=lambda week: week[1], default=None)
    return {
        'longest_distance': longest,
        'best_week': best_week and {'start': best_week[0], 'calories_kcal': best_week[1]},
        'longest_streak': longest_streak(done.order_by('date').values_list('date', flat=True).distinct()),
    }


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
        total_calories_kcal=Sum('calories_kcal'),
        training_days=Count('date', distinct=True, filter=Q(exercise_type__tracks_metrics=True)),
        rest_days=Count(
            'date', distinct=True, filter=Q(exercise_type__tracks_metrics=False) & ~Q(status=Status.SKIPPED)
        ),
    )
    by_exercise = list(
        sessions.exclude(status=Status.SKIPPED)
        .values(exercise=F('exercise_type__name'))
        .annotate(
            sessions=Count('id'),
            total_minutes=Sum('actual_duration_minutes'),
            average_minutes=Avg('actual_duration_minutes'),
            total_distance_km=Sum('actual_distance_km'),
            total_calories_kcal=Sum('calories_kcal'),
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
    calories = sum(a['session'].calories_kcal or 0 for entry in week for a in entry['activities'] if a['session'])
    return {
        'done': done,
        'target': len(training),
        'percent': round(100 * done / len(training)) if training else 0,
        'calories': calories,
    }


def calorie_goal_progress(calories, goal):
    if not goal:
        return None
    return {
        'calories': calories,
        'goal': goal,
        'remaining': max(0, goal - calories),
        'percent': min(100, round(100 * calories / goal)),
    }
