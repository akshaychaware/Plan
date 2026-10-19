from django.core.exceptions import PermissionDenied


def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


def require_admin(user):
    if not is_admin(user):
        raise PermissionDenied('Only administrators can change training plans.')


def access(request):
    """Template context processor exposing the admin flag to every template."""
    return {'is_admin': is_admin(request.user)}
