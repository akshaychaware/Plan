import time

from django.core.cache import cache
from django.db import transaction
from django.db.models.signals import post_delete, post_save

VERSION_KEY = 'plan_app:data-version'


def data_version():
    """Changes on every write to training data; part of every cache key so a write makes old entries unreachable."""
    return cache.get_or_set(VERSION_KEY, time.time_ns, None)


def invalidate(**kwargs):
    """Bump now and again after commit, so a read racing an open transaction can't cache pre-commit data."""
    cache.set(VERSION_KEY, time.time_ns(), None)
    transaction.on_commit(lambda: cache.set(VERSION_KEY, time.time_ns(), None))


def connect_invalidation(*models):
    for model in models:
        post_save.connect(invalidate, sender=model, dispatch_uid=f'invalidate-{model._meta.label}-save')
        post_delete.connect(invalidate, sender=model, dispatch_uid=f'invalidate-{model._meta.label}-delete')
