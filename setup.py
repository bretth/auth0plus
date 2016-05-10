#!/usr/bin/env python
# -*- coding: utf-8 -*-


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'requests',
]

test_requirements = [

]

setup(
    name='auth0plus',
    version='0.2.3',
    description="Unofficial enhancements to the Auth0-python package",
    long_description=readme + '\n\n' + history,
    author="Brett Haydon",
    author_email='brett@haydon.id.au',
    url='https://github.com/bretth/auth0plus',
    packages=[
        'auth0plus',
        'auth0plus.management'
    ],
    package_dir={'auth0plus':
                 'auth0plus'},
    include_package_data=True,
    install_requires=requirements,
    license="ISCL",
    zip_safe=False,
    keywords='auth0plus',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
)
