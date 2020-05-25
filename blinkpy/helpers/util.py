"""Useful functions for blinkpy."""

import json
import logging
import time
import secrets
from calendar import timegm
from functools import wraps
from getpass import getpass
import dateutil.parser
from blinkpy.helpers import constants as const


_LOGGER = logging.getLogger(__name__)


def json_load(file_name):
    """Load json credentials from file."""
    try:
        with open(file_name, "r") as json_file:
            data = json.load(json_file)
        return data
    except FileNotFoundError:
        _LOGGER.error("Could not find %s", file_name)
    except json.decoder.JSONDecodeError:
        _LOGGER.error("File %s has improperly formatted json", file_name)
    return None


def json_save(data, file_name):
    """Save data to file location."""
    with open(file_name, "w") as json_file:
        json.dump(data, json_file, indent=4)


def gen_uid(size):
    """Create a random sring."""
    full_token = secrets.token_hex(size)
    return full_token[0:size]


def time_to_seconds(timestamp):
    """Convert TIMESTAMP_FORMAT time to seconds."""
    try:
        dtime = dateutil.parser.isoparse(timestamp)
    except ValueError:
        _LOGGER.error("Incorrect timestamp format for conversion: %s.", timestamp)
        return False
    return timegm(dtime.timetuple())


def get_time(time_to_convert=None):
    """Create blink-compatible timestamp."""
    if time_to_convert is None:
        time_to_convert = time.time()
    return time.strftime(const.TIMESTAMP_FORMAT, time.gmtime(time_to_convert))


def merge_dicts(dict_a, dict_b):
    """Merge two dictionaries into one."""
    duplicates = [val for val in dict_a if val in dict_b]
    if duplicates:
        _LOGGER.warning(
            ("Duplicates found during merge: %s. " "Renaming is recommended."),
            duplicates,
        )
    return {**dict_a, **dict_b}


def prompt_login_data(data):
    """Prompt user for username and password."""
    if data["username"] is None:
        data["username"] = input("Username:")
    if data["password"] is None:
        data["password"] = getpass("Password:")

    return data


def validate_login_data(data):
    """Check for missing keys."""
    data["uid"] = data.get("uid", gen_uid(const.SIZE_UID))
    data["notification_key"] = data.get(
        "notification_key", gen_uid(const.SIZE_NOTIFICATION_KEY)
    )
    data["device_id"] = data.get("device_id", const.DEVICE_ID)

    return data


class BlinkException(Exception):
    """Class to throw general blink exception."""

    def __init__(self, errcode):
        """Initialize BlinkException."""
        super().__init__()
        self.errid = errcode[0]
        self.message = errcode[1]


class BlinkAuthenticationException(BlinkException):
    """Class to throw authentication exception."""


class BlinkURLHandler:
    """Class that handles Blink URLS."""

    def __init__(self, region_id):
        """Initialize the urls."""
        if region_id is None:
            raise TypeError
        self.subdomain = f"rest-{region_id}"
        self.base_url = f"https://{self.subdomain}.{const.BLINK_URL}"
        self.home_url = f"{self.base_url}/homescreen"
        self.event_url = f"{self.base_url}/events/network"
        self.network_url = f"{self.base_url}/network"
        self.networks_url = f"{self.base_url}/networks"
        self.video_url = f"{self.base_url}/api/v2/videos"
        _LOGGER.debug("Setting base url to %s.", self.base_url)


class Throttle:
    """Class for throttling api calls."""

    def __init__(self, seconds=10):
        """Initialize throttle class."""
        self.throttle_time = seconds
        self.last_call = 0

    def __call__(self, method):
        """Throttle caller method."""

        def throttle_method():
            """Call when method is throttled."""
            return None

        @wraps(method)
        def wrapper(*args, **kwargs):
            """Wrap that checks for throttling."""
            force = kwargs.pop("force", False)
            now = int(time.time())
            last_call_delta = now - self.last_call
            if force or last_call_delta > self.throttle_time:
                result = method(*args, *kwargs)
                self.last_call = now
                return result

            return throttle_method()

        return wrapper
