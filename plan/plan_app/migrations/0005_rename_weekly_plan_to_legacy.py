from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('plan_app', '0004_seed_bike_cycle'),
    ]

    operations = [
        migrations.RenameModel('TrainingPlan', 'LegacyWeeklyPlan'),
    ]
