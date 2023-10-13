"""Generates constants for use in blinkpy."""

import importlib.metadata

__version__ = importlib.metadata.version("blinkpy")

"""
URLS
"""
BLINK_URL = "immedia-semi.com"
DEFAULT_URL = f"rest-prod.{BLINK_URL}"
BASE_URL = f"https://{DEFAULT_URL}"
LOGIN_ENDPOINT = f"{BASE_URL}/api/v5/account/login"

"""
Dictionaries
"""
ONLINE = {"online": True, "offline": False}

"""
OTHER
"""
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/71.0.3578.98 Safari/537.36"
)
DEVICE_ID = "Blinkpy"
TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S%z"
DEFAULT_MOTION_INTERVAL = 1
DEFAULT_REFRESH = 30
MIN_THROTTLE_TIME = 2
SIZE_NOTIFICATION_KEY = 152
SIZE_UID = 16
TIMEOUT = 10
TIMEOUT_MEDIA = 90
