from rest_framework.decorators import api_view
from rest_framework.response import Response

from plan_app.core.api import resolve_dog

from .services import PERIODS, summarize


@api_view(['GET'])
def statistics(request):
    period = request.query_params.get('period', 'all')
    return Response(summarize(resolve_dog(request), period if period in PERIODS else 'all'))
