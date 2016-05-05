from ..exceptions import (
    UnimplementedException,
    MultipleObjectsReturned,
    ObjectDoesNotExist)

from ..settings import AUTH0_PER_PAGE
from .base_endpoints import CRUDEndPoint, QueryableMixin
from .queryset import QuerySet


class User(QueryableMixin, CRUDEndPoint):

    _default_connection = ''  # set by Auth0
    _default_client_id = ''
    _path = 'users'
    _updatable = [
        'blocked',
        'email_verified',
        'email',
        'verify_email',
        'password',
        'phone_number',
        'phone_verified',
        'verify_password',
        'user_metadata',
        'app_metadata',
        'username'
    ]

    class DoesNotExist(ObjectDoesNotExist):
        pass

    def __init__(self, **kwargs):
        try:  # do not store password in __dict__
            self.password = kwargs.pop('password')
        except KeyError:
            pass
        self._connection = kwargs.pop('connection', self._default_connection)
        self._client_id = kwargs.pop('client_id', self._default_client_id)
        super(User, self).__init__(**kwargs)

    @classmethod
    def all(cls, per_page=AUTH0_PER_PAGE, sort=None, connection='', include_totals=True,
            fields=[], include_fields=True):

        params = {
            'per_page': per_page,
            'include_totals': include_totals,
            'sort': sort,
            'connection': connection or cls._default_connection,
            'fields': ','.join(fields) or None,
            'include_fields': include_fields,
        }
        return QuerySet(cls, **params)

    @classmethod
    def create(cls, **kwargs):
        instance = cls(**kwargs)
        instance.save()
        return instance

    @classmethod
    def get(cls, id=None, **kwargs):
        if id:
            try:
                data = cls._client.get(cls.get_url(id), params=kwargs, timeout=cls._timeout)[0]
                user = cls(**data)
                user._fetched = True
                return user
            except IndexError:
                raise User.DoesNotExist("User Does Not Exist")
        else:
            kwargs['per_page'] = 1
            kwargs['include_totals'] = True
            qs = cls.query(**kwargs)
            if qs.count() > 1:
                raise MultipleObjectsReturned("User.get returned multiple users")  # replace
            try:
                return qs[0]
            except IndexError:
                raise User.DoesNotExist("User Does Not Exist")

    @classmethod
    def get_or_create(cls, defaults=None, **kwargs):
        defaults = defaults or {}
        if kwargs:
            try:
                user = cls.get(**kwargs)
                created = False
                return user, created
            except cls.DoesNotExist:
                defaults.update(kwargs)
        user = cls.create(**defaults)
        created = True
        return user, created

    @classmethod
    def query(cls, **kwargs):
        params = {}
        search_engine = kwargs.pop('search_engine', 'v2')
        connection = kwargs.get('connection', cls._default_connection)
        if search_engine == 'v1':
            params.update(kwargs)
            params['search_engine'] = 'v1'
            if params.get('q', None):
                raise UnimplementedException('v1 search engine does not allow q')
            kwargs = {}
        elif kwargs.get('q', None):
            params['search_engine'] = search_engine
        elif search_engine == 'v2' and connection and not kwargs.get('q', None):
            params['search_engine'] = search_engine
            kwargs['q'] = {'identities.connection': connection}
            try:
                del kwargs['connection']
            except KeyError:
                pass

        return super(User, cls).query(params, **kwargs)

    @property
    def password(self):
        """Get the new unsaved password."""
        if hasattr(self, '_password'):
            return self._password
        raise AttributeError("'User' object does not have a new password")

    @password.setter
    def password(self, value):
        """Set a password to be changed or created"""
        self._password = value

    @password.deleter
    def password(self):
        self._original.pop('password', None)
        del self._password

    def get_id(self):
        return getattr(self, 'user_id', None)

    def save(self):
        data = self.get_changed()
        if self._fetched:
            changed = dict(data)
            attrs = data.keys()
            # Cannot update password and email simultaneously
            # Cannot update password and email_verified simultaneously
            # Cannot update username and password simultaneously
            if 'password' in attrs and \
                    ('email' in attrs or 'username' in attrs or 'email_verified' in attrs):
                patch_pass = {'password': data.pop('password'), 'connection': self._connection}
                self._client.patch(self.get_url(), patch_pass, timeout=self._timeout)
            # Cannot update username and email simultaneously
            # Cannot update username and email_verified simultaneously
            if 'username' in attrs and ('email' in attrs or 'email_verified' in attrs):
                patch_user = {'username': data.pop('username'), 'connection': self._connection}
                self._client.patch(self.get_url(), patch_user, timeout=self._timeout)
            if data:
                # supply connection if any of these are to be updated
                conn_set = set(['email_verified', 'phone_verified', 'username', 'password'])
                attr_set = set(data.keys())
                conn_set.intersection_update(attr_set)
                if conn_set:
                    data['connection'] = self._connection
                # also supply client_id if any of these are to be updated
                client_id_set = set(['email', 'phone_number'])
                client_id_set.intersection_update(attr_set)
                if client_id_set:
                    data['client_id'] = self._client_id
                    data['connection'] = self._connection
                self._client.patch(self.get_url(), data, timeout=self._timeout)
            self._original.update(changed)
        else:
            data['connection'] = self._connection
            data = self._client.post(self._endpoint, data, timeout=self._timeout)
            self.__dict__.update(data)
            self._original.update(self.as_dict(updatable_only=True))
            self._fetched = True
        try:  # once saved the password should be deleted
            del self.password
        except AttributeError:
            pass





