"""Generates constants for use in blinkpy."""

import os

MAJOR_VERSION = 0
MINOR_VERSION = 10
PATCH_VERSION = 1

__version__ = '{}.{}.{}'.format(MAJOR_VERSION, MINOR_VERSION, PATCH_VERSION)

REQUIRED_PYTHON_VER = (3, 5, 3)

PROJECT_NAME = 'blinkpy'
PROJECT_PACKAGE_NAME = 'blinkpy'
PROJECT_LICENSE = 'MIT'
PROJECT_AUTHOR = 'Kevin Fronczak'
PROJECT_COPYRIGHT = ' 2017, {}'.format(PROJECT_AUTHOR)
PROJECT_URL = 'https://github.com/fronzbot/blinkpy'
PROJECT_EMAIL = 'kfronczak@gmail.com'
PROJECT_DESCRIPTION = ('A Blink camera Python library '
                       'running on Python 3.')
PROJECT_LONG_DESCRIPTION = ('blinkpy is an open-source '
                            'unofficial API for the Blink Camera '
                            'system with the intention for easy '
                            'integration into various home '
                            'automation platforms.')
if os.path.exists('README.rst'):
    PROJECT_LONG_DESCRIPTION = open('README.rst').read()
PROJECT_CLASSIFIERS = [
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Operating System :: OS Independent',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Topic :: Home Automation'
]

PROJECT_GITHUB_USERNAME = 'fronzbot'
PROJECT_GITHUB_REPOSITORY = 'blinkpy'

PYPI_URL = 'https://pypi.python.org/pypi/{}'.format(PROJECT_PACKAGE_NAME)

'''
URLS
'''
BLINK_URL = 'immedia-semi.com'
LOGIN_URL = 'https://prod.' + BLINK_URL + '/login'
LOGIN_BACKUP_URL = 'https://rest.piri/' + BLINK_URL + '/login'
BASE_URL = 'https://prod.' + BLINK_URL
DEFAULT_URL = 'prod.' + BLINK_URL

'''
Dictionaries
'''
ONLINE = {'online': True, 'offline': False}
