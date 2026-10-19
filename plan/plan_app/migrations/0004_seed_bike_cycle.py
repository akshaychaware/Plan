from django.db import migrations


def seed_bike_cycle(apps, schema_editor):
    ExerciseType = apps.get_model('plan_app', 'ExerciseType')
    ExerciseType.objects.get_or_create(name='Bike/Cycle', defaults={'tracks_metrics': True})


class Migration(migrations.Migration):

    dependencies = [
        ('plan_app', '0003_distance_and_plan_details'),
    ]

    operations = [
        migrations.RunPython(seed_bike_cycle, migrations.RunPython.noop),
    ]
