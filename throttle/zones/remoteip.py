import hashlib

class RemoteIP:
    def __init__(self, **config):
        pass

    def get_bucket_key(self, request, view_func, view_args, view_kwargs):
        """
        Return our best crack at the remote IP address
        """
        key = request.META.get('HTTP_X_FORWARDED_FOR', "") or request.META.get('REMOTE_ADDR')
        return hashlib.md5(key).hexdigest()
