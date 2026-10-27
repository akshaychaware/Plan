from rest_framework import mixins, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from plan_app.core.api import IsSuperuserOrReadOnly

from . import services
from .models import TrainingPlan
from .serializers import TrainingPlanDaySerializer, TrainingPlanSerializer


class TrainingPlanViewSet(
    mixins.ListModelMixin, mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = TrainingPlanSerializer
    permission_classes = [permissions.IsAuthenticated, IsSuperuserOrReadOnly]

    def get_queryset(self):
        plans = TrainingPlan.objects.all()
        dog_id = self.request.query_params.get('dog')
        return plans.filter(dog_id=dog_id) if dog_id and dog_id.isdigit() else plans

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        return Response(self.get_serializer(services.activate_plan(self.get_object(), request.user)).data)

    @action(detail=True, methods=['get', 'put'])
    def days(self, request, pk=None):
        plan = self.get_object()
        if request.method == 'PUT':
            serializer = TrainingPlanDaySerializer(data=request.data, many=True)
            serializer.is_valid(raise_exception=True)
            services.save_week(
                plan, {day['day_of_week']: day['activities'] for day in serializer.validated_data}, request.user
            )
        days = plan.days.prefetch_related('activities__exercise_type')
        return Response(TrainingPlanDaySerializer(days, many=True).data)
