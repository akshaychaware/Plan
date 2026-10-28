from django.core.exceptions import NON_FIELD_ERRORS, ValidationError as DjangoValidationError
from rest_framework import permissions, serializers
from rest_framework.generics import get_object_or_404
from rest_framework.views import exception_handler as drf_exception_handler

from plan_app.dog.models import Dog

from .access import is_admin


def exception_handler(exc, context):
    if isinstance(exc, DjangoValidationError):
        detail = (
            {('non_field_errors' if key == NON_FIELD_ERRORS else key): value for key, value in exc.message_dict.items()}
            if hasattr(exc, 'error_dict') else {'non_field_errors': exc.messages}
        )
        exc = serializers.ValidationError(detail)
    return drf_exception_handler(exc, context)


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS or is_admin(request.user)


def resolve_dog(request):
    dogs = Dog.objects.all()
    dog_id = request.query_params.get('dog')
    if dog_id:
        return get_object_or_404(dogs, pk=dog_id)
    if len(dogs) == 1:
        return dogs[0]
    raise serializers.ValidationError({'dog': 'Specify ?dog=<id>.'})
