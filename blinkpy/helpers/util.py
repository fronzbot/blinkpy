"""Useful functions for blinkpy."""

import logging
import time
from functools import wraps
from requests import Request, Session, exceptions
from blinkpy.helpers.constants import BLINK_URL, TIMESTAMP_FORMAT
import blinkpy.helpers.errors as ERROR


_LOGGER = logging.getLogger(__name__)


def get_time(time_to_convert=None):
    """Create blink-compatible timestamp."""
    if time_to_convert is None:
        time_to_convert = time.time()
    return time.strftime(TIMESTAMP_FORMAT, time.gmtime(time_to_convert))


def merge_dicts(dict_a, dict_b):
    """Merge two dictionaries into one."""
    duplicates = [val for val in dict_a if val in dict_b]
    if duplicates:
        _LOGGER.warning(("Duplicates found during merge: %s. "
                         "Renaming is recommended."), duplicates)
    return {**dict_a, **dict_b}


def create_session():
    """Create a session for blink communication."""
    sess = Session()
    return sess


def attempt_reauthorization(blink):
    """Attempt to refresh auth token and links."""
    _LOGGER.info("Auth token expired, attempting reauthorization.")
    headers = blink.get_auth_token(is_retry=True)
    return headers


def http_req(blink, url='http://example.com', data=None, headers=None,
             reqtype='get', stream=False, json_resp=True, is_retry=False):
    """
    Perform server requests and check if reauthorization neccessary.

    :param blink: Blink instance
    :param url: URL to perform request
    :param data: Data to send (default: None)
    :param headers: Headers to send (default: None)
    :param reqtype: Can be 'get' or 'post' (default: 'get')
    :param stream: Stream response? True/FALSE
    :param json_resp: Return JSON response? TRUE/False
    :param is_retry: Is this a retry attempt? True/FALSE
    """
    if reqtype == 'post':
        req = Request('POST', url, headers=headers, data=data)
    elif reqtype == 'get':
        req = Request('GET', url, headers=headers)
    else:
        _LOGGER.error("Invalid request type: %s", reqtype)
        raise BlinkException(ERROR.REQUEST)

    prepped = req.prepare()

    try:
        response = blink.session.send(prepped, stream=stream, timeout=10)
        if json_resp and 'code' in response.json():
            if is_retry:
                _LOGGER.error("Cannot obtain new token for server auth.")
                return None
            else:
                headers = attempt_reauthorization(blink)
                if not headers:
                    raise exceptions.ConnectionError
                return http_req(blink, url=url, data=data, headers=headers,
                                reqtype=reqtype, stream=stream,
                                json_resp=json_resp, is_retry=True)
    except (exceptions.ConnectionError, exceptions.Timeout):
        _LOGGER.info("Cannot connect to server with url %s.", url)
        if not is_retry:
            headers = attempt_reauthorization(blink)
            return http_req(blink, url=url, data=data, headers=headers,
                            reqtype=reqtype, stream=stream,
                            json_resp=json_resp, is_retry=True)
        _LOGGER.error("Endpoint %s failed. Possible issue with Blink servers.",
                      url)
        return None

    if json_resp:
        return response.json()

    return response


class BlinkException(Exception):
    """Class to throw general blink exception."""

    def __init__(self, errcode):
        """Initialize BlinkException."""
        super().__init__()
        self.errid = errcode[0]
        self.message = errcode[1]


class BlinkAuthenticationException(BlinkException):
    """Class to throw authentication exception."""


class BlinkURLHandler():
    """Class that handles Blink URLS."""

    def __init__(self, region_id, legacy=False):
        """Initialize the urls."""
        self.subdomain = 'rest-{}'.format(region_id)
        if legacy:
            self.subdomain = 'rest.{}'.format(region_id)
        self.base_url = "https://{}.{}".format(self.subdomain, BLINK_URL)
        self.home_url = "{}/homescreen".format(self.base_url)
        self.event_url = "{}/events/network".format(self.base_url)
        self.network_url = "{}/network".format(self.base_url)
        self.networks_url = "{}/networks".format(self.base_url)
        self.video_url = "{}/api/v2/videos".format(self.base_url)
        _LOGGER.debug("Setting base url to %s.", self.base_url)


class Throttle():
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
            force = kwargs.pop('force', False)
            now = int(time.time())
            last_call_delta = now - self.last_call
            if force or last_call_delta > self.throttle_time:
                result = method(*args, *kwargs)
                self.last_call = now
                return result

            return throttle_method()

        return wrapper
