from django.db import migrations, models
from django.db.models import OuterRef, Subquery


def backfill_calories(apps, schema_editor):
    ExerciseType = apps.get_model('plan_app', 'ExerciseType')
    TrainingSession = apps.get_model('plan_app', 'TrainingSession')
    TrainingSession.objects.exclude(status='SKIPPED').update(calories_kcal=Subquery(
        ExerciseType.objects.filter(pk=OuterRef('exercise_type_id')).values('average_calories_kcal')[:1]
    ))


class Migration(migrations.Migration):

    dependencies = [
        ('plan_app', '0011_seed_average_calories'),
    ]

    operations = [
        migrations.AddField(
            model_name='trainingsession',
            name='calories_kcal',
            field=models.DecimalField(blank=True, decimal_places=1, editable=False, max_digits=6, null=True, verbose_name='calories (kcal)'),
        ),
        migrations.RunPython(backfill_calories, migrations.RunPython.noop),
    ]
