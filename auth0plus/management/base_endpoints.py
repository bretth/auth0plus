from copy import deepcopy

from combomethod import combomethod
from six.moves.urllib.parse import quote

from ..exceptions import UnimplementedException
from ..settings import AUTH0_PER_PAGE
from .queryset import QuerySet


class BaseEndPoint(object):

    _endpoint = ''  # set by Auth0 to the base url + _path
    _client = None  # the requests.session set by Auth0 instance
    _timeout = None  # set by Auth0 instance on the subclass
    _path = ''  # set by the implementing subclass
    _updatable = None

    def __init__(self, **kwargs):
        self._fetched = False  # True when loaded from endpoint
        self._original = {}  # allow diffing changes after creation

        # attributes to always exclude from post/patch
        self._private_attrs = []
        self._private_attrs = list(self.__dict__.keys())

        # set the public attributes
        self.__dict__.update(kwargs)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.get_id() == other.get_id()

    def __repr__(self):
        return '<%s %s>' % (
               self.__class__.__name__,
               self.get_id() or '')

    @combomethod
    def get_url(receiver, id=None):
        try:
            id = receiver.get_id()
        except TypeError:
            pass
        if id:
            return '/'.join([receiver._endpoint, quote(str(id))])
        return receiver._endpoint
            
    def _get_public_attrs(self):
        public = list(set(self.__dict__.keys()) - set(self._private_attrs))
        return public

    def get_changed(self):
        data = {}
        if self._updatable is None:
            updatable = self._get_public_attrs()
        else:  # an empty or other list is treated as definitive
            updatable = self._updatable
        for item in updatable:
            try:
                value = getattr(self, item)
            except AttributeError:
                continue
            try:
                if value != self._original[item]:
                    data[item] = value
            except KeyError:
                data[item] = value
        return deepcopy(data)

    def get_id(self):
        return getattr(self, 'id', None)
    
    def as_dict(self, updatable_only=False):
        public_dict = {
            key: value for key, value in self.__dict__.items()
            if key[0] != '_' and key not in self._private_attrs}
        if updatable_only and isinstance(self._updatable, list):
            public_dict = {
                key: value for key, value in public_dict.items()
                if key in self._updatable}
        return deepcopy(public_dict)


class CreatableMixin(object):

    _timeout = None
    
    @classmethod
    def create(cls, **kwargs):
        instance = cls(**kwargs)
        instance.save()
        return instance

    def save(self):
        data = {}
        for key in self._get_public_attrs():
            try:
                data[key] = self.__dict__[key]
            except KeyError:
                pass
        response = self._client.post(self._endpoint, data, timeout=self._timeout)
        self.__dict__.update(response)
        self._fetched = True


class UpdatableMixin(object):

    _updatable = None  # None = all (or not set), empty list is actually zero
    
    def save(self, params=None):
        data = params or {}
        if not self._fetched:
            raise UnimplementedException("This endpoint only supports patch updates")
        if self._updatable is None:  # just assume we can update it all
            updatable = self._get_public_attrs()
        else:  # an empty or other list is treated as definitive
            updatable = self._updatable
        for item in updatable:
            try:
                if self.__dict__[item] != self._original[item]:
                    data[item] = self.__dict__[item]
            except KeyError:
                data[item] = self.__dict__[item]
        if data:
            self._client.patch(self.get_url(), data)


def _build_lucene_query(kwargs):
    lucene_q = []
    for key, value in kwargs.items():
        if '*' in value:
            lucene_q.append(u'%s:%s' % (key, value))
        else:
            lucene_q.append(u'%s:"%s"' % (key, value))
    return ' AND '.join(lucene_q)


class QueryableMixin(object):

    @classmethod
    def query(cls, params=None, **kwargs):
        params = params or {}
        fields = kwargs.pop('fields', None)
        params['fields'] = fields
        if fields:
            include_fields = kwargs.pop('include_fields', True)
            params['include_fields'] = include_fields
        params['page'] = kwargs.pop('page', 0)
        params['per_page'] = kwargs.pop('per_page', AUTH0_PER_PAGE)
        params['sort'] = kwargs.pop('sort', None)
        params['include_totals'] = kwargs.pop('include_totals', True)

        # custom q overrides default
        custom_q = kwargs.pop('q', None)
        # a subclass may pass through a dict to get processed by this class
        if isinstance(custom_q, dict):
            kwargs.update(custom_q)
            custom_q = None
        # whatever kwargs are remaining should be lucene queryable
        params['q'] = custom_q or _build_lucene_query(kwargs) or None
        return QuerySet(cls, **params)


class CRUDEndPoint(UpdatableMixin, CreatableMixin, BaseEndPoint):

    def __init__(self, **kwargs):
        BaseEndPoint.__init__(self, **kwargs)

    @combomethod
    def delete(receiver, id=None):
        try:
            id = receiver.get_id()
        except TypeError:
            pass
        assert id is not None, (
            "%s object can't be deleted because its primary id attribute is set to None." %
            receiver.__class__.__name__
        )
        receiver._client.delete('/'.join([receiver._endpoint, str(id)]), timeout=receiver._timeout)

    def save(self, params=None):
        if self._fetched:
            UpdatableMixin.save(self, params=params)
        else:
            CreatableMixin.save(self, params=params)
