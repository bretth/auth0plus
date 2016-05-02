import os
import time
import unittest

import requests
from dotenv import load_dotenv

from auth0plus.exceptions import Auth0Error, MultipleObjectsReturned
from auth0plus.management.auth0p import Auth0
from auth0plus.management.users import User

load_dotenv('.env')
skip = int(os.getenv('SKIP_INTEGRATION_TESTS', 1))


class IntegrationTestCase(unittest.TestCase):
    @unittest.skipIf(skip, 'SKIP_INTEGRATION_TESTS==1')
    def setUp(self):
        self.session = requests.session()
        self.domain = os.getenv('DOMAIN')
        self.connection = os.getenv('CONNECTION')
        self.client_id = os.getenv('CLIENT_ID')
        self.auth0 = Auth0(
            self.domain,
            os.getenv('JWT'),
            client_id=self.client_id,
            connection=self.connection,
            session=self.session
        )


class TestUserCreate(IntegrationTestCase):

    def setUp(self):
        
        super(TestUserCreate, self).setUp()
        # delete any existing user
        url = 'https://%s/api/v2/users' % self.domain
        params = {
            'q': 'identities.connection:"%s" AND email:"angus@acdc.com"' % self.connection,
            'search_engine': 'v2'}
        resp = self.auth0._client.get(url, params=params)
        try:
            uid = resp[0]['user_id']
            url = '/'.join([url, uid])
        except IndexError:
            return
        resp = self.auth0._client.delete(url)

    def test_get_or_create(self):
        defaults = {'email_verified': True, 'password': "JailBreak"}
        user1, created1 = self.auth0.users.get_or_create(
            defaults=defaults,
            email='angus@acdc.com')
        self.assertTrue(created1)
        time.sleep(3)
        self.assertTrue(user1.get_id().startswith('auth0|'))
        user2, created2 = self.auth0.users.get_or_create(
            defaults=defaults,
            email='angus@acdc.com')
        self.assertFalse(created2)

        self.assertEqual(user1, user2)


class BaseTestWithUsers(IntegrationTestCase):
    def setUp(self):
        super(BaseTestWithUsers, self).setUp()
        url = 'https://%s/api/v2/users' % self.domain
        self.users = [{
            'connection': self.connection,
            'email': 'angus@acdc.com',
            'password': 'JailBreak',
            'email_verified': True},
            {
            'connection': self.connection,
            'email': 'malcolm@acdc.com',
            'password': 'ChuckBerry',
            'email_verified': True}]
        for user in self.users:
            try:
                self.auth0._client.post(url, data=user)
            except Auth0Error as err:
                if err.status_code == 400 and 'The user already exists.' in err.message:
                    continue
                else:
                    raise


class TestUserQuery(BaseTestWithUsers):

    def test_query(self):
        time.sleep(5)  # wait for users to be indexed for search
        all_users = self.auth0.users.all()
        self.assertGreaterEqual(all_users.count(), 2)
        self.assertTrue(all_users[-1].get_id().startswith('auth0|'))
        all_users = self.auth0.users.query(email='*@acdc.com')
        self.assertGreaterEqual(all_users.count(), 2)
        with self.assertRaises(User.DoesNotExist):
            self.auth0.users.get(email='dave@acdc.com')
        with self.assertRaises(MultipleObjectsReturned):
            self.auth0.users.get()
        angus = self.auth0.users.get(email='angus@acdc.com')
        also_angus = self.auth0.users.get(user_id=angus.get_id())
        self.assertEqual(also_angus, angus)
        






