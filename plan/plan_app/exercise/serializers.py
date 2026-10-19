from rest_framework import serializers

from .models import ExerciseType


class ExerciseTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseType
        fields = ['id', 'name', 'description', 'tracks_metrics', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
