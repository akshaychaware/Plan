from django.db import migrations
from django.utils import timezone


def seed_first_weigh_ins(apps, schema_editor):
    Dog = apps.get_model('plan_app', 'Dog')
    WeightEntry = apps.get_model('plan_app', 'WeightEntry')
    today = timezone.localdate()
    for dog in Dog.objects.filter(weight_kg__isnull=False, weights__isnull=True):
        WeightEntry.objects.create(dog=dog, date=today, weight_kg=dog.weight_kg, notes='Starting weight')


class Migration(migrations.Migration):

    dependencies = [
        ('plan_app', '0015_weight_entry'),
    ]

    operations = [
        migrations.RunPython(seed_first_weigh_ins, migrations.RunPython.noop),
    ]
