from rest_framework import mixins, permissions, viewsets

from plan_app.core.api import IsAdminOrReadOnly

from .models import ExerciseType
from .serializers import ExerciseTypeSerializer


class ExerciseTypeViewSet(
    mixins.ListModelMixin, mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = ExerciseType.objects.all()
    serializer_class = ExerciseTypeSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]
