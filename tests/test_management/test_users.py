# -*- coding: utf-8 -*-
import unittest
import mock
from auth0plus.settings import AUTH0_PER_PAGE
from auth0plus.management.users import User
from auth0plus.exceptions import UnimplementedException, MultipleObjectsReturned


class TestUser1(unittest.TestCase):

    def setUp(self):
        User._default_connection = 'test-conn'
        User._client = mock.Mock()
        User._client.get = mock.Mock(return_value=[{'id': 1, 'email': 'malcolm@äcdc.com'}])

    def tearDown(self):
        User._default_connection = ''

    @mock.patch('auth0plus.management.users.User.save')
    def test_create(self, mock_creatable):
        user = User.create(email="malcolm@äcdc.com")
        self.assertTrue(isinstance(user, User))
        self.assertEqual(user.email, "malcolm@äcdc.com")

    @mock.patch('auth0plus.management.users.QueryableMixin.query')
    def test_empty_query(self, mock_qry):
        User.query()
        args, kwargs = mock_qry.call_args
        self.assertEqual(kwargs['q'], {'identities.connection': 'test-conn'})
        self.assertEqual(args[0]['search_engine'], 'v2')

    @mock.patch('auth0plus.management.users.QueryableMixin.query')
    def test_v1_query(self, mock_qry):
        User.query(search_engine='v1')
        args, kwargs = mock_qry.call_args
        self.assertEqual(args[0], {'search_engine': 'v1'})

    def test_unimplemented_query(self):
        with self.assertRaises(UnimplementedException):
            User.query(search_engine='v1', q='email:"bon@äcdc.com"')

    @mock.patch('auth0plus.management.users.QueryableMixin.query')
    def test_query_no_connection_filter(self, mock_qry):
        User._default_connection = ''
        User.query()
        args, kwargs = mock_qry.call_args
        self.assertEqual(kwargs, {})

    def test_get_by_id(self):
        user = User.get(id=1)
        self.assertEqual(user.email, 'malcolm@äcdc.com')

    @mock.patch('auth0plus.management.users.QuerySet', new=mock.Mock, create=False)
    def test_all(self):
        users = User.all()
        self.assertEqual(users.per_page, AUTH0_PER_PAGE)
        self.assertEqual(users.connection, 'test-conn')

    def test_get_id(self):
        user = User()
        user.get_id()


class TestUserGetDoesNotExist(unittest.TestCase):
        def setUp(self):
            qs = mock.MagicMock()
            qs.count.return_value = 0
            qs.__getitem__.side_effect = IndexError()
            patch1 = mock.patch(
                'auth0plus.management.users.User.query',
                return_value=qs)
            self.query = patch1.start()
            self.addCleanup(patch1.stop)

        def test_get_none(self):
            with self.assertRaises(User.DoesNotExist):
                User.get()


class TestUserGetMultipleObjects(unittest.TestCase):
        def setUp(self):
            qs = mock.Mock()
            qs.count.return_value = 2
            patch1 = mock.patch(
                'auth0plus.management.users.User.query',
                return_value=qs)
            self.query = patch1.start()
            self.addCleanup(patch1.stop)

        def test_get_multiple(self):
            with self.assertRaises(MultipleObjectsReturned):
                User.get()


class TestUserGetOrCreateDoesNotExist(unittest.TestCase):
    def setUp(self):
        patch1 = mock.patch(
            'auth0plus.management.users.User.get',
            side_effect=User.DoesNotExist())
        patch2 = mock.patch(
            'auth0plus.management.users.User.create',
            return_value=User(id=1, email='bon@äcdc.com'))
        self.get = patch1.start()
        self.create = patch2.start()
        self.addCleanup(mock.patch.stopall)

    def test_get_or_create_doesnotexist(self):
        user, created = User.get_or_create(email='bon@äcdc.com')
        self.assertTrue(created)
        self.assertEqual(user.email, 'bon@äcdc.com')


class TestUserGetOrCreateGot(unittest.TestCase):
    def setUp(self):
        patch1 = mock.patch(
            'auth0plus.management.users.User.get',
            return_value=User(id=1, email='bon@äcdc.com'))
        self.get = patch1.start()
        self.addCleanup(mock.patch.stopall)

    def test_get_or_create_got_user(self):
        user, created = User.get_or_create(email='bon@äcdc.com')
        self.assertFalse(created)
        self.assertEqual(user.email, 'bon@äcdc.com')


class TestUserSave(unittest.TestCase):
    def setUp(self):
        patch1 = mock.patch('auth0plus.management.users.User._client')
        self.client = patch1.start()
        self.client.post.return_value = {'nickname': None, 'user_id': '1'}
        self.addCleanup(mock.patch.stopall)

    def test_save_new_user(self):
        usr = User(email='axl@äcdc.com', email_verified=True, password='sweetchild')
        usr.save()
        self.assertTrue(self.client.post.called)
        self.assertEqual(
            self.client.post.call_args[0][1],
            {
                'email': 'axl@äcdc.com',
                'password': 'sweetchild',
                'email_verified': True,
                'connection': ''
            })
        self.assertTrue(usr._fetched)
        with self.assertRaises(AttributeError):
            usr.password
        self.assertEqual(
            usr.as_dict(),
            {'email': 'axl@äcdc.com', 'nickname': None, 'email_verified': True, 'user_id': '1'})
        self.assertEqual(usr.get_changed(), {})


class TestUserSaveChanged(unittest.TestCase):
    def setUp(self):
        patch1 = mock.patch('auth0plus.management.users.User._client')
        self.client = patch1.start()
        self.usr = User(email='axl@äcdc.com', email_verified=True, user_id='1')
        self.usr._fetched = True
        self.usr._original.update(self.usr.as_dict())
        self.addCleanup(mock.patch.stopall)

    def test_save_changed_password(self):
        self.assertEqual(self.usr.get_changed(), {})
        self.usr.password = 'CanISitNextToYouGirl'
        self.usr.save()
        self.client.patch.assert_called_with(
            'https://example.com/api/v2/users/1',
            {'password': 'CanISitNextToYouGirl', 'connection': ''}, timeout=10)
        self.assertEqual(self.client.patch.call_count, 1)

    def test_save_changed_password_and_email(self):
        self.assertEqual(self.usr.get_changed(), {})
        self.usr.password = 'CanISitNextToYouGirl'
        self.usr.email = 'brian@äcdc.com'
        self.usr.save()
        kwargs1 = self.client.patch.call_args_list[0][0][1]
        self.assertEqual(
            kwargs1,
            {'password': 'CanISitNextToYouGirl', 'connection': ''})
        kwargs2 = self.client.patch.call_args_list[1][0][1]
        self.assertEqual(kwargs2, {
            'email': 'brian@äcdc.com',
            'connection': '',
            'client_id': ''})

    def test_save_changed_password_and_email_and_username(self):
        self.assertEqual(self.usr.get_changed(), {})
        self.usr.password = 'CanISitNextToYouGirl'
        self.usr.email = 'brian@äcdc.com'
        self.usr.username = 'brian'
        self.usr.user_metadata = {'first_name': 'Brian'}
        self.usr.save()
        self.assertEqual(self.client.patch.call_count, 3)
        kwargs1 = self.client.patch.call_args_list[0][0][1]
        kwargs2 = self.client.patch.call_args_list[1][0][1]
        kwargs3 = self.client.patch.call_args_list[2][0][1]
        self.assertEqual(
            kwargs1,
            {'password': 'CanISitNextToYouGirl', 'connection': ''})
        self.assertEqual(
            kwargs2,
            {'username': 'brian', 'connection': ''})
        self.assertEqual(
            kwargs3,
            {
                'email': 'brian@äcdc.com',
                'client_id': '',
                'connection': '',
                'user_metadata': {'first_name': 'Brian'}})

        



