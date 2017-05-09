===============================
Auth0+ python
===============================


.. image:: https://img.shields.io/pypi/v/auth0plus.svg
        :target: https://pypi.python.org/pypi/auth0plus

.. image:: https://img.shields.io/travis/bretth/auth0plus.svg
        :target: https://travis-ci.org/bretth/auth0plus

.. image:: https://coveralls.io/repos/github/bretth/auth0plus/badge.svg?branch=master :target: https://coveralls.io/github/bretth/auth0plus?branch=master


An unofficial python interface for the Auth0 management api v2 that speeds up integration in python projects.

* Free software: ISC license


Installation
------------
::

    $ pip install auth0plus

Usage
------

To get started with the simplest scenario which is using Auth0 to store a database of users to authenticate against you need to configure a domain and a non-interactive client to access a connection (database). You will also need a JSON web token (jwt) for the client application to access the parts of the api you specify (scopes). This can be generated manually or as I will show here it can be programmatically granted every 24 hours by a separate call to an oauth/token endpoint:

- Login to auth0.com
- Go to the `clients menu <https://manage.auth0.com/#/clients>`_
- Create a client and click on it's settings to get the *Domain* *Client ID* and *Client Secret*
- Go to the `APIs menu <https://manage.auth0.com/#/apis`_ and click *Auth0 Management API*
- Click *Non Interactive Clients* and authorise your client then expand the selection to select scopes.
- Select read:users, update:users, delete:users, create:users, read:users_app_metadata, update:users_app_metadata, delete:users_app_metadata, create:users_app_metadata and create:user_tickets then *update*.

For more information on the above process read `<https://auth0.com/docs/api/management/v2/tokens>`_.

In your code import the Auth0 class.
::
    >>> from auth0plus.management import Auth0
    >>> from auth0plus.oauth import get_token

This example doctest uses python-dotenv to hold the secrets and variables in a .env file.
::
    >>> import os
    >>> from dotenv import load_dotenv
    >>> load_dotenv('.env')
    True
    >>> domain = os.getenv('DOMAIN')
    >>> client_id = os.getenv('CLIENT_ID')
    >>> client_secret = os.getenv('CLIENT_SECRET')
    >>> db = os.getenv('CONNECTION')

Get the 24 hour jwt token dictionary which you would normally store somewhere::

    >>> token = get_token(domain, client_id, client_secret)

Create the lazy connection. We're going to connect to a database backed store.
::
    >>> auth0 = Auth0(domain, token['access_token'], client_id=client_id, default_connection=db)

The api follows the documented api for v2. So the endpoint of /api/v2/users is going to be *auth0.users*, and to get an empty user instance you would call the constructor.
::
    >>> user = auth0.users()

Now we'll actually create a few users for my 4 year old's favourite band:

1. In one step using the endpoint *create* method.
::
    >>> angus = auth0.users.create(email='angus.young@acdc.com', email_verified=True,
    ...     password='Jailbreak', user_metadata={'family_name': 'Young'})

2. With the convience *get_or_create* method which follows the django equivalent.
::
    >>> malcolm, created = auth0.users.get_or_create(
    ...     defaults={'email_verified': True, 'password': 'ChuckB',
    ...     'user_metadata': {'family_name': 'Young'}}, email='malcolm.young@acdc.com')
    >>> malcolm.user_metadata
    {'family_name': 'Young'}
    >>> malcolm.picture
    'https://s.gravatar.com/avatar/...'

3. In two steps with init and *save*.
::
    >>> singer = auth0.users(email='dave.evans@acdc.com', email_verified=True,
    ...     password='CanISitNextToYouGirl')
    >>> singer.save()
    >>> print(singer.user_id)
    auth0|...

*Save* also updates the user (which may need to make multiple calls to the endpoint).
::
    >>> singer.email = 'bon.scott@acdc.com'
    >>> singer.password = 'HighwayToHell'
    >>> singer.save()

One thing to note is that the password is not available once it's saved.
::
    >>> singer.password
    Traceback (most recent call last):
      File "/Library/Frameworks/Python.framework/Versions/3.5/lib/python3.5/doctest.py", line 1320, in __run
        compileflags, 1), test.globs)
      File "<doctest README.rst[21]>", line 1, in <module>
        singer.password
      File ".../auth0plus/auth0plus/management/users.py", line 118, in password
        raise AttributeError("'User' object does not have a new password")
    AttributeError: 'User' object does not have a new password

To distinguish between a User instance that has been created locally and one that has been fetched from Auth0 the boolean attribute *_fetched* determines whether saving the record would be an update (*``_``fetched == True*) or a create (*_fetched == False*).

The *get* classmethod allows returning a single instance, and class specific *ObjectDoesNotExist* exception (*User.DoesNotExist*) if it doesn't exist.
::
    >>> try:
    ...     brian = auth0.users.get(email='brian.johnson@acdc.com')
    ... except auth0.users.DoesNotExist as err:
    ...     print(err)
    User Does Not Exist

    >>> brian, created = auth0.users.get_or_create(
    ...     defaults={'email_verified': True, 'password': 'BackInBlack'},
    ...     email='brian.johnson@acdc.com')


The *get* method uses the auth0 lucene search which means for anything other than the id you can potentially get multiple results (and a *MultipleObjectsReturned* exception), but beware you also need to ensure enough time has passed for newly created users to be indexed.
::
    >>> from auth0plus.exceptions import MultipleObjectsReturned
    >>> import time
    >>> time.sleep(5)
    >>> try:
    ...     singers = auth0.users.get(email='b*')
    ... except MultipleObjectsReturned as err:
    ...     print(err)
    User.get returned multiple users

When you actually want multiple results use a *query* or *all* which return a sliceable lazy object.
::
    >>> singers = auth0.users.query(email='b*')
    >>> singers.count()  # the total returned by include_totals=true, no iteration necessary
    2
    >>> singers[:]  # evaluate the whole query
    [<User auth0|...>, <User auth0|...>]

You can also construct your own 'q' syntax instead of keyword arguments and pass additional endpoint parameters. In this case we'll just get the user_id and email.
::
    >>> brothers = auth0.users.query(
    ...     q='user_metadata.family_name:"Young"',
    ...     fields='user_id,email')
    >>> brothers.count()
    2

If you want to do something with the user data returned then *as_dict* is your friend.
::
    >>> serialized = brothers[0].as_dict()

To maintain state such as whether it has been *_fetched* from auth0 you would pickle the instance, otherwise *as_dict* is the safer choice to reconstitute the object making no assumptions about any changes that might have been made.
::
    >>> new_angus = auth0.users(**serialized)
    >>> new_angus.password = 'MoneyTrain'
    >>> from auth0plus.exceptions import Auth0Error
    >>> try:
    ...     new_angus.save()
    ... except Auth0Error as err:
    ...     print(err)
    400: The user already exists.

Delete instances with classmethods or instance method.
::
    >>> singer.delete()  # Remove Bon Scott
    >>> auth0.users.delete(brian.get_id())

Get all the remaining band members (and delete them). Sorry Angus, it's time to retire.
::
    >>> band = auth0.users.all()
    >>> band.count()
    2
    >>> for member in band:
    ...     member.delete()


Credits
---------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
