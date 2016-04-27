# -*- coding: utf-8 -*-
from ..exceptions import UnimplementedException


class QuerySet(object):
    """
    Generate an iterator over the response and cache the result for slicing like a list.
    """

    def __init__(self, cls, **params):
        self._per_page = params.get('per_page', 0)
        self._page = params.get('page', 0)
        self._len = 0
        self._count = 0
        self._cls = cls
        self._cached = []
        # get an initial response
        response = cls._client.get(cls._endpoint, params)
        # get totals
        try:
            self._total = response[0]['total']
            self._limit = response[0]['limit']
            del params['include_totals']  # we only want to get the totals once
            self._response = response[0][cls._path]
        except (IndexError, KeyError):  # response not wrapped in include_totals summary
            self._total = -1
            self._limit = 0
            self._response = response
        self._len = len(self._response)
        self._params = params

    def __getitem__(self, index):
        if isinstance(index, slice):
            stop = index.stop
        elif isinstance(index, int):
            stop = index
        else:
            raise TypeError
        if stop is not None and stop > -1:
            iterations = stop - len(self._cached) + 1
            try:
                for i in range(iterations):
                    self.__next__()
            except StopIteration:
                pass
        else:  # get all the iterations
            while True:
                try:
                    self.__next__()
                except StopIteration:
                    break
        return self._cached[index]

    def __iter__(self):
        return self

    def __next__(self):
        record = self.next()
        self._cached.append(record)
        return record

    def count(self):
        if self._total > -1:
            return self._total
        # in the simple case if the code hasn't tried to get per_page or include_totals then we'll
        # assume we've received all the records because we can't make any assumptions about
        # how many records the endpoint actually returns by default
        elif not self._per_page or (self._per_page and self._count < self._per_page):
            return len(self._response)
        raise UnimplementedException("include_totals is not implemented on this endpoint")

    def next(self):
        if self._count < self._len:
            item = self._response.pop(0)
            instance = self._cls(**item)
            instance._fetched = True
            self._count += 1
            return instance
        elif self._per_page and self._count == self._per_page:
            self._page += 1
            self._count = 0
            self._params['page'] = self._page
            self._response = self._cls._client.get(self._cls._endpoint, self._params)
            self._len = len(self._response)
            return self.next()
        elif self._per_page and self._count > self._per_page:
            raise UnimplementedException("per_page is not implemented on this endpoint")
        raise StopIteration()
