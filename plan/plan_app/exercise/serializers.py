from rest_framework import serializers

from .models import ExerciseType


class ExerciseTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseType
        fields = ['id', 'name', 'description', 'tracks_metrics', 'average_calories_kcal', 'calories_basis', 'calories_basis_amount', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def validate(self, attrs):
        session = ExerciseType.CaloriesBasis.SESSION
        basis = attrs.get('calories_basis', getattr(self.instance, 'calories_basis', session))
        amount = attrs.get('calories_basis_amount', getattr(self.instance, 'calories_basis_amount', None))
        if basis != session and not amount:
            raise serializers.ValidationError(
                {'calories_basis_amount': 'Required for distance or duration based calories.'}
            )
        return attrs
