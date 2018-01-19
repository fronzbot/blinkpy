# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
from blinkpy.helpers.constants import (
    __version__, PROJECT_PACKAGE_NAME, PROJECT_LICENSE, PROJECT_URL,
    PROJECT_EMAIL, PROJECT_DESCRIPTION, PROJECT_CLASSIFIERS, PROJECT_AUTHOR,
    PROJECT_LONG_DESCRIPTION
)

REQUIRES = [
    'requests>=2.12.4'
]

PACKAGES = find_packages()

setup(
    name = PROJECT_PACKAGE_NAME,
    version = __version__,
    description = PROJECT_DESCRIPTION,
    long_description = PROJECT_LONG_DESCRIPTION,
    author = PROJECT_AUTHOR,
    author_email = PROJECT_EMAIL,
    license = PROJECT_LICENSE,
    url = PROJECT_URL,
    platforms = 'any',
    py_modules = ['blinkpy'],
    packages=PACKAGES,
    install_requires = REQUIRES,
    test_suite = 'tests',
    classifiers = PROJECT_CLASSIFIERS
)
