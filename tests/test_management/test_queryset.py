# -*- coding: utf-8 -*-
import unittest
from mock import Mock, patch

from auth0plus.management.queryset import QuerySet
from auth0plus.exceptions import UnimplementedException

f0 = []

f1 = {
  "start": 0,
  "limit": 50,
  "length": 3,
  "total": 3,
  "users": [
    {"email": "brian@äcdc.com"},
    {"email": "bon@äcdc.com"},
    {"email": "malcolm@äcdc.com"}
  ]
}

f2 = [
    {"email": "brian@äcdc.com"},
    {"email": "bon@äcdc.com"},
    {"email": "malcolm@äcdc.com"}
]

f3a = [{
  "start": 0,
  "limit": 2,
  "length": 2,
  "total": 3,
  "users": [
    {"email": "brian@äcdc.com"},
    {"email": "bon@äcdc.com"},

  ]
}]

f3b = [{"email": "malcolm@äcdc.com"}]


class TestQuerySet(unittest.TestCase):

    def setUp(self):
        class EndPoint(object):
            _endpoint = '/users'
            _path = 'users'
            _client = Mock()
            _client.get = Mock()
            _client.get.return_value = []

            def __init__(self, **kwargs):
                self.__dict__.update(kwargs)
        self.cls = EndPoint

    def tearDown(self):
        pass

    def test_empty(self):
        self.cls._client.get.return_value = f0
        qs = QuerySet(self.cls, per_page=50)
        self.assertEqual(qs[:], [])

    def test_init_with_include_totals(self):
        self.cls._client.get.return_value = [dict(f1)]
        qs = QuerySet(self.cls, per_page=50, include_totals=True)
        self.assertEqual(qs._total, 3)
        self.assertEqual(qs._limit, 50)
        self.assertEqual(qs._len, 3)
        self.assertEqual(qs._params,  {'per_page': 50})

    def test_init_without_include_totals(self):
        self.cls._client.get.return_value = f2
        qs = QuerySet(self.cls, per_page=50, include_totals=False)
        self.assertEqual(qs._total, -1)

    def test_when_total_exceeds_length(self):
        self.cls._client.get.return_value = f3a
        qs = QuerySet(self.cls, per_page=2, include_totals=True)
        self.assertEqual(qs._total, 3)
        self.assertEqual(qs._len, 2)
        # the unconsumed response should have 2 records in it
        self.assertEqual(len(qs._response), 2)
        self.assertEqual(qs[1].email, "bon@äcdc.com")
        # after extracting the last record the response should be empty
        self.assertEqual(qs._response, [])
        # and the response should now be cached
        self.assertEqual(len(qs._cached), 2)

        self.cls._client.get.return_value = f3b
        # get the remaining record
        self.assertEqual(qs[2].email, "malcolm@äcdc.com")
        self.assertEqual(len(qs._cached), 3)
        args, kwargs = self.cls._client.get.call_args
        self.assertIn('per_page', args[1].keys())
        # include_totals should be removed from any remaining response
        self.assertNotIn('include_totals', args[1].keys())

    def test__getitem__raises_typeerror(self):
        with self.assertRaises(TypeError):
            qs = QuerySet(self.cls, per_page=50)
            qs['mate!']

    @patch('auth0plus.management.queryset.QuerySet.__next__', side_effect=StopIteration)
    def test__getitem__stopiteration(self, mock_next):
        self.cls._client.get.return_value = [{'email': 'brian@äcdc.com'}]
        qs = QuerySet(self.cls, per_page=50)
        self.assertFalse(mock_next.called)
        try:
            qs[0]
        except IndexError:
            self.assertTrue(mock_next.called)

    def test__iter__(self):
        qs = QuerySet(self.cls)
        qs.__iter__()

    def test_count(self):
        self.cls._client.get.return_value = [dict(f1)]
        qs = QuerySet(self.cls, include_totals=True)
        self.assertEqual(qs.count(), 3)

    def test_include_totals_unimplemented(self):
        self.cls._client.get.return_value = [{"email": "malcolm@äcdc.com"}]
        with self.assertRaises(UnimplementedException):
            qs = QuerySet(self.cls, per_page=10)
            # artificially set the recs returned to longer than what we got
            qs._count = 11
            qs.count()

    def test_count_simple(self):
        self.cls._client.get.return_value = [{"email": "malcolm@äcdc.com"}]
        qs = QuerySet(self.cls, per_page=10)
        # artificially set the recs returned to longer than what we got
        self.assertEqual(qs.count(), 1)

    def test_per_page_unimplemented(self):
        self.cls._client.get.return_value = [{"email": "malcolm@äcdc.com"}]
        with self.assertRaises(UnimplementedException):
            qs = QuerySet(self.cls, per_page=10)
            # artificially set the recs returned to longer than what we got
            qs._count = 11
            qs.next()



