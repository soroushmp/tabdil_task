# cache.py
from urllib.parse import urlparse

from django.core.cache import cache
from rest_framework.response import Response


# ──────────────
# Helper functions
# ──────────────

def cache_set(key: str, value, timeout: int = 300):
    """
    Set a value in the cache under `key` for `timeout` seconds.
    """
    cache.set(key, value, timeout)


def cache_get(key: str):
    """
    Retrieve a value from the cache. Returns None if not found.
    """
    return cache.get(key)


def cache_delete(key: str):
    """
    Delete a value from the cache.
    """
    cache.delete(key)


# ──────────────
# DRF Mixin
# ──────────────

class CacheMixin:
    """
    Mixin for DRF ModelViewSet (or any ViewSet) that:
      • Caches GET-list and GET-detail
      • Invalidates cache on create/update/partial_update/destroy
      • Provides manual invalidation methods
    """

    # default cache timeout (seconds); override per-view if needed
    cache_timeout: int = 300

    def list(self, request, *args, **kwargs):
        key = self._list_cache_key(request)
        data = cache_get(key)
        if data is None:
            response = super().list(request, *args, **kwargs)
            if response.status_code == 200:
                cache_set(key, response.data, self.cache_timeout)
            return response
        return Response(data)

    def retrieve(self, request, *args, **kwargs):
        pk = kwargs.get(self.lookup_field, kwargs.get('pk'))
        key = self._detail_cache_key(request, pk)
        data = cache_get(key)
        if data is None:
            response = super().retrieve(request, *args, **kwargs)
            if response.status_code == 200:
                cache_set(key, response.data, self.cache_timeout)
            return response
        return Response(data)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        # clear list cache so new item will appear
        if response.status_code in (200, 201):
            cache_delete(self._list_cache_key(request))
        return response

    def _invalidate_all_list_caches(self, request):
        """
        Invalidate all possible list cache variations by using a pattern.
        This is needed because list caches might have different query parameters.
        """
        # Get base cache key without query params
        parsed = urlparse(request.path)
        path_parts = parsed.path.rstrip('/').split('/')
        base_path = '/'.join(path_parts[:-1]) + '/' if len(path_parts) > 1 else '/'
        base_key = f"{self.__class__.__name__}:list:{base_path}"
        # If using redis, we can delete all keys matching the pattern
        if hasattr(cache, 'keys'):
            try:
                # Get all keys matching the base pattern
                keys = cache.keys(f"{base_key}*")
                if keys:
                    cache.delete_many(keys)
                return
            except (AttributeError, NotImplementedError):
                pass

        # Fallback: delete the exact key (with current query params)
        cache_delete(self._list_cache_key(request))

    def update(self, request, *args, **kwargs):
        pk = kwargs.get(self.lookup_field, kwargs.get('pk'))
        # Get instance before update for any cleanup if needed
        instance = self.get_object()
        response = super().update(request, *args, **kwargs)
        # clear both detail and all list caches
        if response.status_code == 200:
            cache_delete(self._detail_cache_key(request, pk))
            self._invalidate_all_list_caches(request)

            # If there are any related caches, invalidate them too
            if hasattr(self, 'invalidate_related_caches'):
                self.invalidate_related_caches(instance)

        return response

    def partial_update(self, request, *args, **kwargs):
        # partial_update semantics are same as update for caching
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        # Get instance before deletion for cleanup
        instance = self.get_object()
        pk = kwargs.get(self.lookup_field, kwargs.get('pk'))
        response = super().destroy(request, *args, **kwargs)
        # clear caches if delete succeeded
        if response.status_code == 204:
            cache_delete(self._detail_cache_key(request, pk))
            self._invalidate_all_list_caches(request)

            # If there are any related caches, invalidate them too
            if hasattr(self, 'invalidate_related_caches'):
                self.invalidate_related_caches(instance)

        return response

    # ──────────────
    # Manual invalidation
    # ──────────────

    def invalidate_list_cache(self, request):
        """Call this to clear the cached list for the current request."""
        cache_delete(self._list_cache_key(request))

    def invalidate_detail_cache(self, request, pk):
        """Call this to clear the cached detail for a given `pk`."""
        cache_delete(self._detail_cache_key(request, pk))

    def invalidate_related_caches(self, instance):
        for cache_key in self._get_instance_related_caches(instance):
            # If using redis, we can delete all keys matching the pattern
            if hasattr(cache, 'keys'):
                try:
                    # Get all keys matching the base pattern
                    keys = cache.keys(cache_key)
                    if keys:
                        cache.delete_many(keys)
                except (AttributeError, NotImplementedError):
                    pass

    # ──────────────
    # Cache-key builders
    # ──────────────

    def _list_cache_key(self, request) -> str:
        # include path to namespace list caches
        return f"{self.__class__.__name__}:list:{request.get_full_path()}"

    def _detail_cache_key(self, request, pk) -> str:
        # include pk and path to namespace per-object caches
        return f"{self.__class__.__name__}:detail:{pk}:{request.get_full_path()}"

    @staticmethod
    def _get_instance_related_caches(instance):
        class_names = {
            'User': 'AdminUserViewSet',
            'Vendor': 'VendorViewSet',
            'PhoneNumber': 'PhoneNumberViewSet',
            'VendorTransaction': 'VendorTransactionViewSet',
            'PhoneNumberTransaction': 'PhoneNumberTransactionViewSet',
        }
        base_key = f"{class_names[instance.__class__.__name__]}"
        return f"*{base_key}:list:*", f"*{base_key}:detail:{instance.pk}:*"
