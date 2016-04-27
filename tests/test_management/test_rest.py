
"""
This is basically just an exploration of how Betamax works
"""
from unittest import TestCase

from mock import Mock

from auth0plus.management.rest import RestClient
from auth0plus.settings import TIMEOUT

HTTP = 'http://httpbin.org/'


class TestRestClient(TestCase):
    def setUp(self):
        self.client = RestClient('123', session=Mock())

    def test_get_bool_conversion(self):
        self.client._process_response = Mock(return_value={})
        resp = self.client.get('/', params={'a_bool': True})
        self.client.requests.get.assert_called_with(
            '/', params={'a_bool': 'true'}, headers={'Content-Type': None}, timeout=TIMEOUT)
        self.assertEqual(resp, [])

    def test_get_none_removal(self):
        self.client._process_response = Mock(return_value={})
        self.client.get('/', params={'a_none': None})
        self.client.requests.get.assert_called_with(
            '/', params={}, headers={'Content-Type': None}, timeout=TIMEOUT)

    def test_get_empty(self):
        self.client.requests.get.return_value.text = '{}'
        self.assertEqual(self.client.get('/'), [])

    def test_get_empty_list(self):
        self.client.requests.get.return_value.text = '[]'
        self.assertEqual(self.client.get('/'), [])

    def test_get_nothing(self):
        self.client.requests.get.return_value.text = ''
        self.assertEqual(self.client.get('/'), [])

    def test_get_single(self):
        self.client.requests.get.return_value.text = '{"name": "Brian"}'
        self.assertEqual(self.client.get('/'), [{"name": "Brian"}])

    def test_get_multiple(self):
        self.client.requests.get.return_value.text = '["a", "b"]'
        self.assertEqual(self.client.get('/'), ["a", "b"])

    def test_post(self):
        self.client._process_response = Mock(return_value={})
        self.client.post('/', {'name': 'Malcolm'})
        self.assertTrue(self.client.requests.post.called)

    def test_patch(self):
        self.client._process_response = Mock(return_value={})
        self.client.patch('/', {'name': 'Malcolm'})
        self.assertTrue(self.client.requests.patch.called)

    def test_delete(self):
        self.client._process_response = Mock(return_value={})
        self.client.delete('/')
        self.assertTrue(self.client.requests.delete.called)

    def test_file_post(self):
        self.client._process_response = Mock(return_value={})
        self.client.file_post('/')
        self.assertTrue(self.client.requests.post.called)








