#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_auth0
----------------------------------

Tests for `management.auth0` module.
"""

import unittest

from auth0plus.management.auth0p import Auth0, _set_endpoint_attributes
from auth0plus.management.users import User


class Test_configure_endpoint(unittest.TestCase):

    def setUp(self):
        class Parent(object):
            pass

        class Endpoint(object):
            _path = 'an-endpoint'

        class ChildEndpoint(object):
            _path = 'parent/child-endpoint'

        class ParentWithKids(object):
            _path = 'parent'
            _endpoints = [ChildEndpoint]

        self.parent = Parent
        self.defaults = {'attribute': 'value'}
        self.endpoint = Endpoint
        self.parentwithkids = ParentWithKids
        self.childendpoint = ChildEndpoint

    def test_endpoint_has_attribute(self):
        _set_endpoint_attributes(self.parent, self.endpoint, self.defaults)
        self.assertEqual(self.endpoint.attribute, 'value')

    def test_endpoint_is_attached_to_parent(self):
        _set_endpoint_attributes(self.parent, self.endpoint, self.defaults)
        self.assertIs(self.parent.an_endpoint, self.endpoint)

    def test_parent_with_kid(self):
        _set_endpoint_attributes(self.parentwithkids, self.childendpoint, self.defaults)
        self.assertIs(self.parentwithkids.child_endpoint, self.childendpoint)

    def test__endpoint_url(self):
        defaults = {'_base_url': 'https://example.com/api/v2'}
        _set_endpoint_attributes(self.parent, self.endpoint, defaults)
        self.assertEqual(self.endpoint._endpoint, 'https://example.com/api/v2/an-endpoint')


class TestAuth0(unittest.TestCase):

    def test_init(self):
        auth0 = Auth0('example.com', '123')
        self.assertIs(auth0.users, User)
