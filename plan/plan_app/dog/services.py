from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum

from .models import Dog, WeightEntry

WEIGH_IN_INTERVAL = timedelta(days=15)


@transaction.atomic
def record_weight(dog, date, weight_kg, notes=''):
    """Save the weigh-in for `date` (replacing one already there) and keep the dog's current weight in sync."""
    entry = dog.weights.filter(date=date).first() or WeightEntry(dog=dog, date=date)
    entry.weight_kg, entry.notes = weight_kg, notes
    entry.full_clean()
    entry.save()
    sync_current_weight(dog)
    return entry


def sync_current_weight(dog):
    latest = dog.weights.values_list('weight_kg', flat=True).first()
    if latest is not None:
        Dog.objects.filter(pk=dog.pk).update(weight_kg=latest)
        dog.weight_kg = latest


def weigh_in_status(dog, today):
    last = dog.weights.first()
    next_due = last.date + WEIGH_IN_INTERVAL if last else today
    return {'last': last, 'next_due': next_due, 'due': next_due <= today}


def weight_log(dog, today):
    """Weigh-ins (newest first), each with the change and kcal burned since the previous weigh-in."""
    entries = list(dog.weights.order_by('date', 'id'))
    daily = dict(dog.sessions.order_by().values_list('date').annotate(kcal=Sum('calories_kcal')))

    def calories_between(start, end):
        return sum((kcal or 0 for day, kcal in daily.items() if start < day <= end), Decimal(0))

    rows, previous = [], None
    for entry in entries:
        rows.append({
            'entry': entry,
            'change_kg': entry.weight_kg - previous.weight_kg if previous else None,
            'calories_kcal': calories_between(previous.date, entry.date) if previous else None,
        })
        previous = entry
    rows.reverse()
    return {'rows': rows, 'calories_since_last': calories_between(previous.date, today) if previous else None}
