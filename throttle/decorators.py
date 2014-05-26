import functools
from django.utils.decorators import available_attrs

from throttle.zones import get_zone
from throttle.exceptions import RateLimitExceeded


def throttle(view_func=None, zone='default', callback=None):
    def _enforce_throttle(func):
        @functools.wraps(func, assigned=available_attrs(view_func))
        def _wrapped_view(request, *args, **kwargs):
            # Get zone from cache
            _throttle_zone = get_zone(zone)

            # raises an exception if the rate limit is exceeded
            try:
                response = _throttle_zone.process_view(request, func, args, kwargs)
            except RateLimitExceeded, e:
                if callback:
                    callback()
                raise e
            return response
        return _wrapped_view

    # Validate the rate limiter bucket
    _zone = get_zone(zone)

    if view_func:
        setattr(view_func, 'throttle_zone', _zone)
        return _enforce_throttle(view_func)
    return _enforce_throttle
