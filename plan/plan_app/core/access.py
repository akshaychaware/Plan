import os

from django.contrib.staticfiles import finders
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext

ASSETS = ('plan_app/style.css', 'plan_app/app.js', 'plan_app/theme.js')


def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


def require_admin(user):
    if not is_admin(user):
        raise PermissionDenied(gettext('Only administrators can make changes.'))


def is_superuser(user):
    return user.is_authenticated and user.is_superuser


def require_superuser(user):
    if not is_superuser(user):
        raise PermissionDenied(gettext('Only superusers can change the plan or edit recorded sessions.'))


def asset_version():
    """Latest modification time of the app's CSS/JS, appended to their URLs so browsers never reuse a stale copy."""
    return max((int(os.path.getmtime(found)) for found in map(finders.find, ASSETS) if found), default=0)


def access(request):
    """Template context processor exposing the admin/superuser flags and the static asset version to every template."""
    return {
        'is_admin': is_admin(request.user), 'is_superuser': is_superuser(request.user),
        'asset_version': asset_version(),
    }
