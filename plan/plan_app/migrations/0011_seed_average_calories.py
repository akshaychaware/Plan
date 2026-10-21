from decimal import Decimal

from django.db import migrations

AVERAGE_CALORIES_KCAL = {
    'Bike/Cycle': Decimal('50'),
    'Swimming': Decimal('70'),
    'Hill Climbing': Decimal('65'),
    'Walking': Decimal('27.5'),
}


def seed_average_calories(apps, schema_editor):
    ExerciseType = apps.get_model('plan_app', 'ExerciseType')
    for name, kcal in AVERAGE_CALORIES_KCAL.items():
        ExerciseType.objects.filter(name=name).update(average_calories_kcal=kcal)


def clear_average_calories(apps, schema_editor):
    ExerciseType = apps.get_model('plan_app', 'ExerciseType')
    ExerciseType.objects.filter(name__in=AVERAGE_CALORIES_KCAL).update(average_calories_kcal=None)


class Migration(migrations.Migration):

    dependencies = [
        ('plan_app', '0010_exercisetype_average_calories_kcal'),
    ]

    operations = [
        migrations.RunPython(seed_average_calories, clear_average_calories),
    ]
