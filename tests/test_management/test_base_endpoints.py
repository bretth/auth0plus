# -*- coding: utf-8 -*-
from unittest import TestCase

from mock import Mock, patch
import six

from auth0plus.settings import AUTH0_PER_PAGE
from auth0plus.management.base_endpoints import (
    BaseEndPoint,
    CreatableMixin,
    UpdatableMixin,
    QueryableMixin,
    _build_lucene_query,
    # _delete,
    CRUDEndPoint)


class TestBaseEndPoint(TestCase):

    def setUp(self):
        BaseEndPoint._endpoint = 'https://example.com/api/v2/an-endpoint'

    def tearDown(self):
        BaseEndPoint._endpoint = ''

    def test_equality(self):
        obj1 = BaseEndPoint(name="Angus")
        obj2 = BaseEndPoint(name="Malcolm")
        self.assertEqual(obj1, obj2)
        obj1.id = 1
        obj2.id = 2
        self.assertNotEqual(obj1, obj2)

    def test_equality_true(self):
        obj1 = BaseEndPoint(name="Angus")
        obj2 = BaseEndPoint(name="Angus")
        self.assertEqual(obj1, obj2)

    def test__repr_no_id(self):
        obj = BaseEndPoint()
        self.assertEqual(obj.__repr__(), '<BaseEndPoint >')

    def test__repr_id(self):
        obj = BaseEndPoint(id=1)
        self.assertEqual(obj.__repr__(), '<BaseEndPoint 1>')

    def test_get_url_with_id(self):
        obj = BaseEndPoint(id=1)
        self.assertEqual(obj.get_url(), 'https://example.com/api/v2/an-endpoint/1')

    def test_cls_get_url_with_id(self):
        url = BaseEndPoint.get_url(id=1)
        self.assertEqual(url, 'https://example.com/api/v2/an-endpoint/1')

    def test_cls_get_url_with_no_id(self):
        url = BaseEndPoint.get_url()
        self.assertEqual(url, 'https://example.com/api/v2/an-endpoint')

    def test__get_public_attrs(self):
        obj = BaseEndPoint(id=1, name='foo')
        six.assertCountEqual(self, obj._get_public_attrs(), ['id', 'name'])

        obj = BaseEndPoint()
        six.assertCountEqual(self, obj._get_public_attrs(), [])

    def test__as_dict(self):
        obj = BaseEndPoint(id=1, name='foo')
        six.assertCountEqual(self, obj.as_dict().items(), [('id', 1), ('name', 'foo')])

    def test_get_id(self):
        obj = BaseEndPoint(id=1)
        self.assertEqual(obj.id, 1)

        self.assertEqual(obj.get_id(), 1)

    def test_get_changed1(self):
        obj = BaseEndPoint(id=1)
        self.assertEqual(obj.get_changed(), {'id': 1})


class TestCreatableMixin(TestCase):
    
    def setUp(self):
        # Mock the RestClient post
        attrs = {'post.return_value': {'id': 1, 'name': 'Brian Johnson'}}
        client = Mock()
        client.configure_mock(**attrs)
        self.creatable = CreatableMixin()
        self.creatable.__dict__['name'] = 'foo'
        self.creatable._client = client
        self.creatable._endpoint = 'river-plate'
        self.creatable._get_public_attrs = Mock(return_value=['name'])

    def test_save(self):
        with self.assertRaises(AttributeError):
            self.creatable.id
        self.creatable.save()
        self.assertEqual(self.creatable.id, 1)
        self.assertEqual(self.creatable.name, 'Brian Johnson')
        self.assertTrue(self.creatable._fetched)


class TestCreatableMixin_create(TestCase):

    def setUp(self):
        class EndPoint(CreatableMixin):
            def __init__(self, *args, **kwargs):
                self.__dict__.update(kwargs)
            save = Mock()
        
        self.EndPoint = EndPoint

    def test_create(self):
        inst = self.EndPoint.create(id=1, name='Bon')
        self.assertTrue(inst.save.called)
        self.assertEqual(inst.id, 1)


class TestUpdatable(TestCase):

    def setUp(self):
        class EndPoint(UpdatableMixin):
            def __init__(self, **kwargs):
                self._endpoint = '/'
                self._fetched = True
                self._updatable = None
                self._original = kwargs
                self.__dict__.update(kwargs)
                # mock the methods
                self._client = Mock()
                self.get_url = Mock(return_value='/')
                self._get_public_attrs = Mock(return_value=['name'])
                self.id = 1

        self.EndPoint = EndPoint

    def test_save_001(self):
        ep = self.EndPoint(id=1, name="Bon Scott")
        ep.name = "Brian Johnson"
        ep.save()
        ep._client.patch.assert_called_with('/', {'name': "Brian Johnson"})

    def test_save_no_changes(self):
        ep = self.EndPoint(id=1, name="Bon Scott")
        ep.save()
        self.assertFalse(ep._client.patch.called)

    def test_save_empty_updatable(self):
        ep = self.EndPoint(id=1, name="Bon Scott")
        ep._updatable = []
        ep.name = "Brian"
        ep.save()
        self.assertFalse(ep._client.patch.called)

    def test_save_defined_updatable_list(self):
        ep = self.EndPoint(id=1, name="Bon Scott")
        ep._updatable = ['name']
        ep.name = "Brian"
        ep.save()
        self.assertTrue(ep._client.patch.called)


class TestCRUDEndPoint(TestCase):
    def setUp(self):
        attrs = {'delete.return_value': 1}
        CRUDEndPoint._client = Mock(**attrs)
        patcher1 = patch('auth0plus.management.base_endpoints.UpdatableMixin')
        patcher2 = patch('auth0plus.management.base_endpoints.CreatableMixin')
        self.MockUpdatable = patcher1.start()
        self.MockCreatable = patcher2.start()
        self.addCleanup(patcher1.stop)
        self.addCleanup(patcher2.stop)

    def tearDown(self):
        CRUDEndPoint._client = None

    def test_save_post(self):
        ep = CRUDEndPoint(name='Bon')
        ep.save()
        self.assertTrue(self.MockCreatable.save.called)

    def test_save_patch(self):
        ep = CRUDEndPoint(name='Bon')
        ep._fetched = True
        ep.name = 'Brian'
        ep.save()
        self.assertTrue(self.MockUpdatable.save.called)

    def test_delete_classmethod(self):
        CRUDEndPoint.delete(1)
        self.assertTrue(CRUDEndPoint._client.delete.called)

    def test_delete_instancemethod(self):
        ep = CRUDEndPoint(id=1, name="Brian")
        ep.delete()
        self.assertTrue(CRUDEndPoint._client.delete.called)


class TestQueryableMixin(TestCase):
    
    def setUp(self):
        patcher1 = patch('auth0plus.management.base_endpoints.QuerySet', new=Mock, create=False)
        patcher2 = patch('auth0plus.management.base_endpoints._build_lucene_query')
        self.MockQS = patcher1.start()
        self.mock_blq = patcher2.start()
        self.addCleanup(patch.stopall)
 
    def test_query_no_params(self):
        mockqs = QueryableMixin.query()
        self.assertEqual(mockqs.include_totals, True)
        self.assertEqual(mockqs.per_page, AUTH0_PER_PAGE)

    def test_with_fields(self):
        mockqs = QueryableMixin.query(fields='xyz,abc')
        self.assertEqual(mockqs.include_fields, True)
        self.assertEqual(mockqs.fields, 'xyz,abc')

    def test_with_custom_q_dict(self):
        QueryableMixin.query(q={'email': u"bonscott@äcdc.com"})
        # _build_lucene_query called with the q
        args, kwargs = self.mock_blq.call_args
        self.assertEqual(args[0], {'email': u"bonscott@äcdc.com"})

    def test_with_custom_q_str(self):
        mockqs = QueryableMixin.query(q=u'email:"bonscott@äcdc.com"')
        # _build_lucene_query not called
        self.assertIsNone(self.mock_blq.call_args)
        # passed through
        self.assertEqual(mockqs.q, u'email:"bonscott@äcdc.com"')


class Test__build_lucene_query(TestCase):

    def test__build_lucene_query_empty(self):
        lq = _build_lucene_query({})
        self.assertEqual(lq, '')

    def test__build_lucene_query(self):
        kwargs = {'email': u"bonscott@äcdc.com"}
        lq = _build_lucene_query(kwargs)
        self.assertEqual(lq, u'email:"bonscott@äcdc.com"')

