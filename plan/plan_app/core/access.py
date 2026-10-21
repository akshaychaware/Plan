import os

from django.contrib.staticfiles import finders
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext

ASSETS = ('plan_app/style.css', 'plan_app/app.js', 'plan_app/theme.js')


def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


def require_admin(user):
    if not is_admin(user):
        raise PermissionDenied(gettext('Only administrators can change training plans.'))


def asset_version():
    """Latest modification time of the app's CSS/JS, appended to their URLs so browsers never reuse a stale copy."""
    return max((int(os.path.getmtime(found)) for found in map(finders.find, ASSETS) if found), default=0)


def access(request):
    """Template context processor exposing the admin flag and the static asset version to every template."""
    return {'is_admin': is_admin(request.user), 'asset_version': asset_version()}
