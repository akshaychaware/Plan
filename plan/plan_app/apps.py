from django.apps import AppConfig


class PlanAppConfig(AppConfig):
    name = 'plan_app'

    def ready(self):
        from .core.cache import connect_invalidation
        from .models import Dog, ExerciseType, PlannedActivity, TrainingPlan, TrainingPlanDay, TrainingSession, WeightEntry

        connect_invalidation(
            Dog, ExerciseType, PlannedActivity, TrainingPlan, TrainingPlanDay, TrainingSession, WeightEntry
        )
