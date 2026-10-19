from django.urls import path
from rest_framework.routers import SimpleRouter

from plan_app.dog.api import DogViewSet
from plan_app.exercise.api import ExerciseTypeViewSet
from plan_app.statistics.api import statistics
from plan_app.training_plan.api import TrainingPlanViewSet
from plan_app.training_session.api import TrainingSessionViewSet, training_today

router = SimpleRouter(trailing_slash=False)
router.register('dogs', DogViewSet, basename='dog')
router.register('exercise-types', ExerciseTypeViewSet, basename='exercise-type')
router.register('training-plans', TrainingPlanViewSet, basename='training-plan')
router.register('training/sessions', TrainingSessionViewSet, basename='training-session')

urlpatterns = [
    path('training/today', training_today, name='training-today'),
    path('training/history', TrainingSessionViewSet.as_view({'get': 'list'}), name='training-history'),
    path('statistics', statistics, name='statistics'),
    *router.urls,
]
