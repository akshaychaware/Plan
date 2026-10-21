from decimal import Decimal

from django.db import migrations

CALORIES = {
    'Bike/Cycle': (Decimal('50'), 'DISTANCE', Decimal('2')),
    'Hill Climbing': (Decimal('65'), 'DISTANCE', Decimal('1')),
    'Walking': (Decimal('27.5'), 'DISTANCE', Decimal('1')),
    'Swimming': (Decimal('70'), 'DURATION', Decimal('20')),
    'Rest': (Decimal('0'), 'SESSION', None),
}


def seed_and_recalculate(apps, schema_editor):
    ExerciseType = apps.get_model('plan_app', 'ExerciseType')
    TrainingSession = apps.get_model('plan_app', 'TrainingSession')
    for name, (kcal, basis, amount) in CALORIES.items():
        ExerciseType.objects.filter(name=name).update(
            average_calories_kcal=kcal, calories_basis=basis, calories_basis_amount=amount
        )
    for session in TrainingSession.objects.exclude(status='SKIPPED').select_related('exercise_type'):
        exercise = session.exercise_type
        kcal = exercise.average_calories_kcal
        if kcal is not None and exercise.calories_basis != 'SESSION':
            actual = (
                session.actual_distance_km if exercise.calories_basis == 'DISTANCE' else session.actual_duration_minutes
            )
            kcal = (kcal * Decimal(actual or 0) / exercise.calories_basis_amount).quantize(Decimal('0.1'))
        TrainingSession.objects.filter(pk=session.pk).update(calories_kcal=kcal)


class Migration(migrations.Migration):

    dependencies = [
        ('plan_app', '0013_calories_basis_and_weekly_goal'),
    ]

    operations = [
        migrations.RunPython(seed_and_recalculate, migrations.RunPython.noop),
    ]
