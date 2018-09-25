"""Useful functions for blinkpy."""

import logging
import requests
import blinkpy.helpers.errors as ERROR
from blinkpy.helpers.constants import BLINK_URL


_LOGGER = logging.getLogger(__name__)


def attempt_reauthorization(blink):
    """Attempt to refresh auth token and links."""
    _LOGGER.debug("Auth token expired, attempting reauthorization.")
    headers = blink.get_auth_token()
    blink.sync.set_links()
    return headers


def http_req(blink, url='http://google.com', data=None, headers=None,
             reqtype='get', stream=False, json_resp=True, is_retry=False):
    """Perform server requests and check if reauthorization neccessary."""
    if reqtype == 'post':
        response = requests.post(url, headers=headers,
                                 data=data)
    elif reqtype == 'get':
        response = requests.get(url, headers=headers,
                                stream=stream)
    else:
        raise BlinkException(ERROR.REQUEST)

    if json_resp and 'code' in response.json():
        if is_retry:
            raise BlinkAuthenticationException(
                (response.json()['code'], response.json()['message']))
        else:
            headers = attempt_reauthorization(blink)
            return http_req(blink, url=url, data=data, headers=headers,
                            reqtype=reqtype, stream=stream,
                            json_resp=json_resp, is_retry=True)
    # pylint: disable=no-else-return
    if json_resp:
        return response.json()
    else:
        return response


# pylint: disable=super-init-not-called
class BlinkException(Exception):
    """Class to throw general blink exception."""

    def __init__(self, errcode):
        """Initialize BlinkException."""
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
