from rest_framework import serializers

from .models import Dog


class DogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dog
        fields = ['id', 'name', 'breed', 'date_of_birth', 'weight_kg', 'notes', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
