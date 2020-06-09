"""Generates constants for use in blinkpy."""

import os

MAJOR_VERSION = 0
MINOR_VERSION = 16
PATCH_VERSION = "0-rc4"

__version__ = f"{MAJOR_VERSION}.{MINOR_VERSION}.{PATCH_VERSION}"

REQUIRED_PYTHON_VER = (3, 6, 0)

PROJECT_NAME = "blinkpy"
PROJECT_PACKAGE_NAME = "blinkpy"
PROJECT_LICENSE = "MIT"
PROJECT_AUTHOR = "Kevin Fronczak"
PROJECT_COPYRIGHT = f" 2017, {PROJECT_AUTHOR}"
PROJECT_URL = "https://github.com/fronzbot/blinkpy"
PROJECT_EMAIL = "kfronczak@gmail.com"
PROJECT_DESCRIPTION = "A Blink camera Python library " "running on Python 3."
PROJECT_LONG_DESCRIPTION = (
    "blinkpy is an open-source "
    "unofficial API for the Blink Camera "
    "system with the intention for easy "
    "integration into various home "
    "automation platforms."
)
if os.path.exists("README.rst"):
    PROJECT_LONG_DESCRIPTION = open("README.rst").read()
PROJECT_CLASSIFIERS = [
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Topic :: Home Automation",
]

PROJECT_GITHUB_USERNAME = "fronzbot"
PROJECT_GITHUB_REPOSITORY = "blinkpy"

PYPI_URL = f"https://pypi.python.org/pypi/{PROJECT_PACKAGE_NAME}"

"""
URLS
"""
BLINK_URL = "immedia-semi.com"
DEFAULT_URL = f"rest-prod.{BLINK_URL}"
BASE_URL = f"https://{DEFAULT_URL}"
LOGIN_ENDPOINT = f"{BASE_URL}/api/v4/account/login"

"""
Dictionaries
"""
ONLINE = {"online": True, "offline": False}

"""
OTHER
"""
DEVICE_ID = "Blinkpy"
TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S%z"
DEFAULT_MOTION_INTERVAL = 1
DEFAULT_REFRESH = 30
MIN_THROTTLE_TIME = 2
SIZE_NOTIFICATION_KEY = 152
SIZE_UID = 16
