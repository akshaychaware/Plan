from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('plan_app', '0007_migrate_weekly_plans'),
    ]

    operations = [
        migrations.RemoveConstraint(model_name='legacyweeklyplan', name='unique_plan_per_dog_weekday'),
        migrations.DeleteModel(name='LegacyWeeklyPlan'),
    ]
