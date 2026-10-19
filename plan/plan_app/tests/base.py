from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from plan_app.models import Dog, ExerciseType, TrainingPlan
from plan_app.training_plan.services import planned_activities_for, save_plan, save_week


class TrackerTestCase(TestCase):
    """`user` is an admin (staff), `other_user` a normal user.

    Luna has an active plan with Swimming (20 min) then Walking (1 km) today and Rest tomorrow.
    """

    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user('owner', password='test-pass-123', is_staff=True)
        cls.other_user = get_user_model().objects.create_user('other', password='test-pass-123')
        cls.dog = Dog.objects.create(owner=cls.user, name='Luna')
        cls.types = {exercise.name: exercise for exercise in ExerciseType.objects.all()}
        cls.today = timezone.localdate()
        cls.plan = save_plan(TrainingPlan(dog=cls.dog, start_date=cls.today - timedelta(days=30)))
        save_week(cls.plan, {
            cls.today.weekday(): [
                {'exercise_type': cls.types['Swimming'], 'planned_duration_minutes': 20},
                {'exercise_type': cls.types['Walking'], 'planned_distance_km': Decimal('1')},
            ],
            (cls.today.weekday() + 1) % 7: [{'exercise_type': cls.types['Rest']}],
        })
        cls.swim, cls.walk = planned_activities_for(cls.dog, cls.today)
