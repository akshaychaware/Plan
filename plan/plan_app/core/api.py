from django.core.exceptions import NON_FIELD_ERRORS, ValidationError as DjangoValidationError
from rest_framework import permissions, serializers
from rest_framework.generics import get_object_or_404
from rest_framework.views import exception_handler as drf_exception_handler


def exception_handler(exc, context):
    if isinstance(exc, DjangoValidationError):
        detail = (
            {('non_field_errors' if key == NON_FIELD_ERRORS else key): value for key, value in exc.message_dict.items()}
            if hasattr(exc, 'error_dict') else {'non_field_errors': exc.messages}
        )
        exc = serializers.ValidationError(detail)
    return drf_exception_handler(exc, context)


class IsStaffOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS or request.user.is_staff


class OwnedDogField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        return self.context['request'].user.dogs.all()


def resolve_dog(request):
    dogs = request.user.dogs.all()
    dog_id = request.query_params.get('dog')
    if dog_id:
        return get_object_or_404(dogs, pk=dog_id)
    if len(dogs) == 1:
        return dogs[0]
    raise serializers.ValidationError({'dog': 'Specify ?dog=<id>.'})
