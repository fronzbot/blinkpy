"""Generates constants for use in blinkpy."""

import importlib.metadata

__version__ = importlib.metadata.version("blinkpy")

"""
URLS
"""
BLINK_URL = "immedia-semi.com"
DEFAULT_URL = f"rest-prod.{BLINK_URL}"
BASE_URL = f"https://{DEFAULT_URL}"
OAUTH_BASE_URL = "https://api.oauth.blink.com"
LOGIN_ENDPOINT = f"{OAUTH_BASE_URL}/oauth/token"
TIER_ENDPOINT = f"{BASE_URL}/api/v1/users/tier_info"

"""
Dictionaries
"""
ONLINE = {"online": True, "offline": False}

"""
OTHER
"""
APP_BUILD = "ANDROID_28373244"
DEFAULT_USER_AGENT = "27.0ANDROID_28373244"
DEVICE_ID = "Blinkpy"
TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S%z"
DEFAULT_MOTION_INTERVAL = 1
DEFAULT_REFRESH = 30
MIN_THROTTLE_TIME = 2
SIZE_NOTIFICATION_KEY = 152
SIZE_UID = 16
TIMEOUT = 10
TIMEOUT_MEDIA = 90

"""
OAuth Constants
"""
OAUTH_CLIENT_ID = "android"
OAUTH_GRANT_TYPE_PASSWORD = "password"
OAUTH_GRANT_TYPE_REFRESH_TOKEN = "refresh_token"
OAUTH_SCOPE = "client"
