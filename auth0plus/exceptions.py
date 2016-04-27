
try:
    from auth0.v2.exceptions import Auth0Error
except ImportError:  # pragma: no cover
    class Auth0Error(Exception):
        def __init__(self, status_code, error_code, message):
            self.status_code = status_code
            self.error_code = error_code
            self.message = message

        def __str__(self):
            return '%s: %s' % (self.status_code, self.message)


class MultipleObjectsReturned(Exception):
    pass


class ObjectDoesNotExist(Exception):
    pass


class DoesNotExist(ObjectDoesNotExist):
    pass


class UnimplementedException(Exception):
    pass

