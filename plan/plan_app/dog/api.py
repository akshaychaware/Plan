from rest_framework import mixins, viewsets

from .serializers import DogSerializer


class DogViewSet(
    mixins.ListModelMixin, mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = DogSerializer

    def get_queryset(self):
        return self.request.user.dogs.all()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
