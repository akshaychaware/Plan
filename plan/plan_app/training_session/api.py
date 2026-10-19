from datetime import date

from django.utils import timezone
from rest_framework import mixins, serializers, viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from plan_app.core.api import resolve_dog

from . import services
from .models import TrainingSession
from .serializers import TrainingSessionSerializer, serialize_day


def parse_date(value, field):
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise serializers.ValidationError({field: 'Use YYYY-MM-DD.'}) from None


class TrainingSessionViewSet(
    mixins.ListModelMixin, mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = TrainingSessionSerializer

    def get_queryset(self):
        params = self.request.query_params
        sessions = TrainingSession.objects.filter(dog__owner=self.request.user).select_related(
            'exercise_type', 'planned_exercise_type'
        )
        if params.get('dog', '').isdigit():
            sessions = sessions.filter(dog_id=params['dog'])
        if params.get('status') in TrainingSession.Status.values:
            sessions = sessions.filter(status=params['status'])
        if params.get('from'):
            sessions = sessions.filter(date__gte=parse_date(params['from'], 'from'))
        if params.get('to'):
            sessions = sessions.filter(date__lte=parse_date(params['to'], 'to'))
        return sessions


@api_view(['GET'])
def training_today(request):
    dog = resolve_dog(request)
    value = request.query_params.get('date')
    day = parse_date(value, 'date') if value else timezone.localdate()
    return Response(serialize_day(dog, services.day_entries(dog, day)))
