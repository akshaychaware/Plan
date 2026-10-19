from django.utils import timezone
from rest_framework import serializers

from plan_app.dog.models import Dog
from plan_app.exercise.models import ExerciseType
from plan_app.training_plan.models import PlannedActivity

from . import services
from .models import TrainingSession


class TrainingSessionSerializer(serializers.ModelSerializer):
    dog_id = serializers.PrimaryKeyRelatedField(source='dog', queryset=Dog.objects.all(), required=False)
    planned_activity_id = serializers.PrimaryKeyRelatedField(
        source='planned_activity', queryset=PlannedActivity.objects.all(), required=False, allow_null=True
    )
    exercise_type_id = serializers.PrimaryKeyRelatedField(
        source='exercise_type', queryset=ExerciseType.objects.all(), required=False
    )
    exercise = serializers.CharField(source='exercise_type.name', read_only=True)
    planned_exercise = serializers.CharField(source='planned_exercise_type.name', read_only=True, default=None)
    date = serializers.DateField(required=False)

    class Meta:
        model = TrainingSession
        fields = [
            'id', 'dog_id', 'planned_activity_id', 'date', 'exercise_type_id', 'exercise', 'status',
            'planned_exercise', 'planned_duration_minutes', 'planned_distance_km', 'planned_repetitions',
            'actual_duration_minutes', 'actual_distance_km', 'actual_repetitions', 'notes',
            'planned_summary', 'actual_summary', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'planned_duration_minutes', 'planned_distance_km', 'planned_repetitions',
            'planned_summary', 'actual_summary', 'created_at', 'updated_at',
        ]
        validators = []

    def create(self, validated_data):
        planned = validated_data.pop('planned_activity', None)
        dog = validated_data.pop('dog', None) or (planned and planned.training_plan_day.training_plan.dog)
        if dog is None:
            raise serializers.ValidationError({'dog_id': 'Required when plannedActivityId is not given.'})
        day = validated_data.pop('date', None) or timezone.localdate()
        return services.record_session(dog=dog, day=day, planned_activity=planned, **validated_data)

    def update(self, instance, validated_data):
        for immutable in ('dog', 'planned_activity', 'date'):
            validated_data.pop(immutable, None)
        return services.save_session(instance, **validated_data)


def serialize_day(dog, entry):
    activities = []
    for activity in entry['activities']:
        planned, session = activity['planned'], activity['session']
        activities.append({
            'planned_activity_id': planned and planned.pk,
            'session_id': session and session.pk,
            'exercise': activity['exercise'].name,
            'exercise_type_id': activity['exercise'].pk,
            'planned_duration_minutes': planned and planned.planned_duration_minutes,
            'planned_distance_km': planned and planned.planned_distance_km,
            'planned_repetitions': planned and planned.planned_repetitions,
            'notes': planned.notes if planned else session.notes,
            'status': activity['status'],
            'actual_duration_minutes': session and session.actual_duration_minutes,
            'actual_distance_km': session and session.actual_distance_km,
            'actual_repetitions': session and session.actual_repetitions,
        })
    return {'date': entry['date'], 'dog': {'id': dog.pk, 'name': dog.name}, 'activities': activities}
