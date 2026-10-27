from rest_framework import mixins, permissions, viewsets

from plan_app.core.api import IsAdminOrReadOnly

from .models import Dog
from .serializers import DogSerializer


class DogViewSet(
    mixins.ListModelMixin, mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Dog.objects.all()
    serializer_class = DogSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
