from rest_framework import mixins, viewsets

from .models import Dog
from .serializers import DogSerializer


class DogViewSet(
    mixins.ListModelMixin, mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Dog.objects.all()
    serializer_class = DogSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
