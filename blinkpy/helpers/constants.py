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
OAuth v2 endpoints (Authorization Code Flow + PKCE)
"""
OAUTH_AUTHORIZE_URL = f"{OAUTH_BASE_URL}/oauth/v2/authorize"
OAUTH_SIGNIN_URL = f"{OAUTH_BASE_URL}/oauth/v2/signin"
OAUTH_2FA_VERIFY_URL = f"{OAUTH_BASE_URL}/oauth/v2/2fa/verify"
OAUTH_TOKEN_URL = f"{OAUTH_BASE_URL}/oauth/token"


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

"""
OAuth v2 parameters
"""
OAUTH_V2_CLIENT_ID = "ios"
OAUTH_REDIRECT_URI = "immedia-blink://applinks.blink.com/signin/callback"

"""
User agents for OAuth v2
"""
OAUTH_USER_AGENT = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
    "Version/26.1 Mobile/15E148 Safari/604.1"
)
OAUTH_TOKEN_USER_AGENT = "Blink/2511191620 CFNetwork/3860.200.71 Darwin/25.1.0"
