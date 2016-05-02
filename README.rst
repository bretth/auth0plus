===============================
Auth0+ python
===============================


.. image:: https://img.shields.io/travis/bretth/auth0plus.svg
        :target: https://travis-ci.org/bretth/auth0plus


An unofficial python interface for the Auth0 management api v2 inspired by django. Currently it just implements the users endpoint.

* Free software: ISC license


Installation
------------
::

    $ pip install auth0plus

Usage
------

To get started you will need your Auth0 domain, client id, and connection to the database that will hold your users. You will also need a JSON web token (jwt):

- Login to auth0.com
- Go to their management api documentation (https://auth0.com/docs/api/v2)
- Add scopes for the actions and entities you wish to access via api (eg create, read, update, and delete actions for the users entity)
- Copy the generated `jwt`.
- Go to the dashboard and get (or setup) your client id, domain, db connection for your test app.

In your code import the Auth0 class::

    >>> from auth0plus.management.auth0p import Auth0

This example doctest uses python-dotenv to hold the secrets and variables in a .env file::

    >>> import os
    >>> from dotenv import load_dotenv 
    >>> load_dotenv('.env')
    True
    >>> domain = os.getenv('DOMAIN')
    >>> client_id = os.getenv('CLIENT_ID')
    >>> connection = os.getenv('CONNECTION')
    >>> jwt = os.getenv('JWT')

Create the lazy connection::

    >>> auth0 = Auth0(domain, jwt, client_id, connection)

The api follows the documented api for v2. So the endpoint of /api/v2/users is going to be *auth0.users*, and to get an empty user instance you would call the constructor::
    
    >>> user = auth0.users() 

Now we'll actually create a few users:

1. In one step using the endpoint create method::

    >>> angus = auth0.users.create(email='angus.young@acdc.com', email_verified=True,
    ...     password='Jailbreak')

2. With the convience *get_or_create* method which will be familiar to django users::

    >>> malcolm, created = auth0.users.get_or_create(
    ...     defaults={'email_verified': True, 'password': 'ChuckB'},
    ...     email='malcolm.young@acdc.com')
    >>> assert created == True

3. In two steps with init and save::

    >>> singer = auth0.users(email='dave.evans@acdc.com', email_verified=True,
    ...     password='CanISitNextToYouGirl')
    >>> singer.save()
    >>> print(singer.user_id)
    auth0|...

Save also updates the user (which may make multiple calls to the endpoint)::

    >>> singer.email = 'bon.scott@acdc.com'
    >>> singer.password = 'HighwayToHell'
    >>> singer.save()

One thing to note is that the password is not available once it's saved::

    >>> singer.password
    Traceback (most recent call last):
      File "/Library/Frameworks/Python.framework/Versions/3.5/lib/python3.5/doctest.py", line 1320, in __run
        compileflags, 1), test.globs)
      File "<doctest README.rst[21]>", line 1, in <module>
        singer.password
      File ".../auth0plus/auth0plus/management/users.py", line 118, in password
        raise AttributeError("'User' object does not have a new password")
    AttributeError: 'User' object does not have a new password

The *get* classmethod allows returning a single instance, and class specific ObjectDoesNotExist exception (User.DoesNotExist) if it doesn't exist::

    >>> try:
    ...     brian = auth0.users.get(email='brian.johnson@acdc.com')
    ... except auth0.users.DoesNotExist as err:
    ...     print(err)
    User Does Not Exist
    
    >>> brian, created = auth0.users.get_or_create(
    ...     defaults={'email_verified': True, 'password': 'BackInBlack'},
    ...     email='brian.johnson@acdc.com')


The _get_ method uses the auth0 lucene search which means for anything other than the id you can potentially get multiple results (and a MultipleObjects exception), but beware you also need to ensure enough time has passed for newly created users to be indexed::

    >>> from auth0plus.exceptions import MultipleObjectsReturned
    >>> import time
    >>> time.sleep(5)
    >>> try:
    ...     singers = auth0.users.get(email='b*')
    ... except MultipleObjectsReturned as err:
    ...     print(err)
    User.get returned multiple users

When you actually want multiple results use a _query_ or _all_ which return a sliceable lazy object::
    
    >>> singers = auth0.users.query(email='b*')
    >>> singers.count()  # the total returned by include_totals=true, no iteration necessary
    2
    >>> singers[:]  # evaluate the whole query
    [<User auth0|...>, <User auth0|...>]

You can also construct your own 'q' syntax instead of keyword arguments and pass additional endpoint parameters::  
    
    >>> bon = auth0.users.query(
    ...     q='email:"bon.scott@acdc.com"', 
    ...     fields='user_id,email')[0]

If you want to do something with the user data returned then *as_dict* is your friend::

    >>> bon.as_dict()['user_id']
    'auth0|...'

Delete instances with classmethods or instance method::

    >>> bon.delete()
    >>> auth0.users.delete(brian.get_id())

Get all the remaining band members::

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
