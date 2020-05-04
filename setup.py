"""Setup file for blinkpy."""
# -*- coding: utf-8 -*-
from os.path import abspath, dirname
from setuptools import setup, find_packages
from blinkpy.helpers.constants import (
    __version__, PROJECT_PACKAGE_NAME, PROJECT_LICENSE, PROJECT_URL,
    PROJECT_EMAIL, PROJECT_DESCRIPTION, PROJECT_CLASSIFIERS, PROJECT_AUTHOR,
)

PROJECT_VERSION = __version__

THIS_DIR = abspath(dirname(__file__))

REQUIRES = [
    "python-dateutil~=2.8.0",
    "requests~=2.23.0",
    "python-slugify~=4.0.0",
]

PACKAGES = find_packages(exclude=['tests*', 'docs'])

with open('{}/README.rst'.format(THIS_DIR), encoding='utf-8') as readme_file:
    LONG_DESCRIPTION = readme_file.read()

setup(
    name=PROJECT_PACKAGE_NAME,
    version=PROJECT_VERSION,
    description=PROJECT_DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    author=PROJECT_AUTHOR,
    author_email=PROJECT_EMAIL,
    license=PROJECT_LICENSE,
    url=PROJECT_URL,
    platforms='any',
    py_modules=['blinkpy'],
    packages=PACKAGES,
    include_package_data=True,
    install_requires=REQUIRES,
    test_suite='tests',
    classifiers=PROJECT_CLASSIFIERS
)
