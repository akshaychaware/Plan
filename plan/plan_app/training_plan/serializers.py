from rest_framework import serializers

from plan_app.dog.models import Dog
from plan_app.exercise.models import ExerciseType

from . import services
from .models import PlannedActivity, TrainingPlan, TrainingPlanDay


class TrainingPlanSerializer(serializers.ModelSerializer):
    dog_id = serializers.PrimaryKeyRelatedField(source='dog', queryset=Dog.objects.all())

    class Meta:
        model = TrainingPlan
        fields = ['id', 'dog_id', 'name', 'start_date', 'end_date', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def create(self, validated_data):
        return services.save_plan(TrainingPlan(**validated_data))

    def update(self, instance, validated_data):
        validated_data.pop('dog', None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        return services.save_plan(instance)


class PlannedActivitySerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    exercise_type_id = serializers.PrimaryKeyRelatedField(source='exercise_type', queryset=ExerciseType.objects.all())
    exercise = serializers.CharField(source='exercise_type.name', read_only=True)

    class Meta:
        model = PlannedActivity
        fields = [
            'id', 'sequence', 'exercise_type_id', 'exercise', 'planned_duration_minutes', 'planned_distance_km',
            'planned_repetitions', 'notes', 'summary',
        ]
        read_only_fields = ['sequence', 'summary']


class TrainingPlanDaySerializer(serializers.ModelSerializer):
    day_name = serializers.CharField(source='get_day_of_week_display', read_only=True)
    activities = PlannedActivitySerializer(many=True)

    class Meta:
        model = TrainingPlanDay
        fields = ['day_of_week', 'day_name', 'activities']
