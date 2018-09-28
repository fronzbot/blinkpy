"""Useful functions for blinkpy."""

import logging
from requests import Request, Session
import blinkpy.helpers.errors as ERROR
from blinkpy.helpers.constants import BLINK_URL


_LOGGER = logging.getLogger(__name__)


def create_session():
    """Create a session for blink communication."""
    sess = Session()
    return sess


def attempt_reauthorization(blink):
    """Attempt to refresh auth token and links."""
    _LOGGER.debug("Auth token expired, attempting reauthorization.")
    headers = blink.get_auth_token()
    blink.sync.set_links()
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
        raise BlinkException(ERROR.REQUEST)

    prepped = req.prepare()
    response = blink.session.send(prepped, stream=stream)

    if json_resp and 'code' in response.json():
        if is_retry:
            raise BlinkAuthenticationException(
                (response.json()['code'], response.json()['message']))
        else:
            headers = attempt_reauthorization(blink)
            return http_req(blink, url=url, data=data, headers=headers,
                            reqtype=reqtype, stream=stream,
                            json_resp=json_resp, is_retry=True)

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

    pass


class BlinkURLHandler():
    """Class that handles Blink URLS."""

    def __init__(self, region_id):
        """Initialize the urls."""
        self.base_url = "https://rest.{}.{}".format(region_id, BLINK_URL)
        self.home_url = "{}/homescreen".format(self.base_url)
        self.event_url = "{}/events/network".format(self.base_url)
        self.network_url = "{}/network".format(self.base_url)
        self.networks_url = "{}/networks".format(self.base_url)
        self.video_url = "{}/api/v2/videos".format(self.base_url)
        _LOGGER.debug("Setting base url to %s.", self.base_url)
