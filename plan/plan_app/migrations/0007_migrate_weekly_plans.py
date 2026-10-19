from django.db import migrations
from django.utils import timezone

STATUS_MAP = {'completed': 'COMPLETED', 'partial': 'PARTIALLY_COMPLETED', 'skipped': 'SKIPPED'}


def migrate_weekly_plans(apps, schema_editor):
    Dog = apps.get_model('plan_app', 'Dog')
    LegacyWeeklyPlan = apps.get_model('plan_app', 'LegacyWeeklyPlan')
    TrainingPlan = apps.get_model('plan_app', 'TrainingPlan')
    TrainingPlanDay = apps.get_model('plan_app', 'TrainingPlanDay')
    PlannedActivity = apps.get_model('plan_app', 'PlannedActivity')
    TrainingSession = apps.get_model('plan_app', 'TrainingSession')

    for old, new in STATUS_MAP.items():
        TrainingSession.objects.filter(status=old).update(status=new)

    for dog in Dog.objects.filter(pk__in=LegacyWeeklyPlan.objects.values('dog')):
        first_session = TrainingSession.objects.filter(dog=dog).order_by('date').values_list('date', flat=True).first()
        start_date = min(filter(None, [timezone.localtime(dog.created_at).date(), first_session]))
        plan = TrainingPlan.objects.create(dog=dog, name='Weekly plan', start_date=start_date, is_active=True)
        days = {day: TrainingPlanDay.objects.create(training_plan=plan, day_of_week=day) for day in range(7)}
        activities = {
            entry.weekday: PlannedActivity.objects.create(
                training_plan_day=days[entry.weekday],
                exercise_type_id=entry.exercise_type_id,
                sequence=0,
                planned_duration_minutes=entry.planned_duration_minutes,
                planned_distance_km=entry.planned_distance_km,
                notes=entry.details,
            )
            for entry in LegacyWeeklyPlan.objects.filter(dog=dog)
        }
        for session in TrainingSession.objects.filter(dog=dog):
            activity = activities.get(session.date.weekday())
            if activity and activity.exercise_type_id == session.planned_exercise_type_id:
                session.planned_activity = activity
                session.save(update_fields=['planned_activity'])


class Migration(migrations.Migration):

    dependencies = [
        ('plan_app', '0006_architecture_schema'),
    ]

    operations = [
        migrations.RunPython(migrate_weekly_plans),
    ]
