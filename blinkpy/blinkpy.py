
# -*- coding: utf-8 -*-
"""
blinkpy by Kevin Fronczak - A Blink camera Python library.

https://github.com/fronzbot/blinkpy
Original protocol hacking by MattTW :
https://github.com/MattTW/BlinkMonitorProtocol
Published under the MIT license - See LICENSE file for more details.
"Blink Wire-Free HS Home Monitoring & Alert Systems" is a trademark
owned by Immedia Inc., see www.blinkforhome.com for more information.
I am in no way affiliated with Blink, nor Immedia Inc.
"""

import time
import json
import getpass
import logging
import blinkpy.helpers.errors as ERROR
from blinkpy.sync_module import BlinkSyncModule
from blinkpy.helpers.util import (
    http_req, create_session, BlinkURLHandler,
    BlinkException, BlinkAuthenticationException)
from blinkpy.helpers.constants import (
    DEFAULT_URL, BLINK_URL, LOGIN_URL, LOGIN_BACKUP_URL)

REFRESH_RATE = 30

_LOGGER = logging.getLogger('blinkpy')


class Blink():
    """Class to initialize communication."""

    def __init__(self, username=None, password=None,
                 refresh_rate=REFRESH_RATE):
        """
        Initialize Blink system.

        :param username: Blink username (usually email address)
        :param password: Blink password
        :param refresh_rate: Refresh rate of blink information.
                             Defaults to 15 (seconds)
        """
        self._username = username
        self._password = password
        self._token = None
        self._auth_header = None
        self._host = None
        self._events = []
        self._last_summary = None
        self._last_events = None
        self.network_id = None
        self.account_id = None
        self.urls = None
        self.sync = None
        self.region = None
        self.region_id = None
        self.last_refresh = None
        self.refresh_rate = refresh_rate
        self.session = None
        self._login_url = LOGIN_URL

    @property
    def events(self):
        """Get all events on server."""
        return self._events

    def start(self):
        """
        Perform full system setup.

        Method logs in and sets auth token, urls, and ids for future requests.
        Essentially this is just a wrapper function for ease of use.
        """
        if self._username is None or self._password is None:
            self.login()
        else:
            self.get_auth_token()

        self.get_ids()
        self.sync = BlinkSyncModule(self, self._auth_header)
        self.sync.get_videos()
        if self.sync.video_count > 0:
            self.sync.get_cameras()
        self.sync.set_links()
        self._events = self.events_request()

    def login(self):
        """Prompt user for username and password."""
        self._username = input("Username:")
        self._password = getpass.getpass("Password:")
        if self.get_auth_token():
            _LOGGER.info("Login successful!")
            return True
        _LOGGER.warning("Unable to login with %s.", self._username)
        return False

    def get_auth_token(self):
        """Retrieve the authentication token from Blink."""
        if not isinstance(self._username, str):
            raise BlinkAuthenticationException(ERROR.USERNAME)
        if not isinstance(self._password, str):
            raise BlinkAuthenticationException(ERROR.PASSWORD)

        headers = {'Host': DEFAULT_URL,
                   'Content-Type': 'application/json'}
        data = json.dumps({
            "email": self._username,
            "password": self._password,
            "client_specifier": "iPhone 9.2 | 2.2 | 222"
        })
        self.session = create_session()
        response = http_req(self, url=self._login_url, headers=headers,
                            data=data, json_resp=False, reqtype='post')
        if response.status_code == 200:
            response = response.json()
            (self.region_id, self.region), = response['region'].items()
        else:
            _LOGGER.debug(
                ("Received response code %s "
                 "when authenticating, "
                 "trying new url"), response.status_code
            )
            self._login_url = LOGIN_BACKUP_URL
            response = http_req(self, url=self._login_url, headers=headers,
                                data=data, reqtype='post')
            self.region_id = 'piri'
            self.region = "UNKNOWN"

        self._host = "{}.{}".format(self.region_id, BLINK_URL)
        self._token = response['authtoken']['authtoken']

        self._auth_header = {'Host': self._host,
                             'TOKEN_AUTH': self._token}

        self.urls = BlinkURLHandler(self.region_id)

        return self._auth_header

    def get_ids(self):
        """Set the network ID and Account ID."""
        response = self._network_request()
        self.network_id = str(response['networks'][0]['id'])
        self.account_id = str(response['networks'][0]['account_id'])

    def _network_request(self):
        """Get network and account information."""
        url = self.urls.networks_url
        headers = self._auth_header
        if headers is None:
            raise BlinkException(ERROR.AUTH_TOKEN)
        return http_req(self, url=url, headers=headers, reqtype='get')

    def events_request(self, skip_throttle=False):
        """Get events on server."""
        url = "{}/{}".format(self.urls.event_url, self.network_id)
        headers = self._auth_header
        if self.check_if_ok_to_update() or skip_throttle:
            self._last_events = http_req(self, url=url,
                                         headers=headers,
                                         reqtype='get')
        return self._last_events

    def summary_request(self, skip_throttle=False):
        """Get blink summary."""
        url = self.urls.home_url
        headers = self._auth_header
        if headers is None:
            raise BlinkException(ERROR.AUTH_TOKEN)
        if self.check_if_ok_to_update() or skip_throttle:
            self._last_summary = http_req(
                self, url=url, headers=headers, reqtype='get')
        return self._last_summary

    def refresh(self, force_cache=False):
        """
        Perform a system refresh.

        :param force_cache: Force an update of the camera cache
        """
        if self.check_if_ok_to_update() or force_cache:
            _LOGGER.debug("Attempting refresh of cameras.")
            self._last_events = self.events_request(skip_throttle=True)
            self._last_summary = self.summary_request(skip_throttle=True)
            self.sync.refresh(force_cache=force_cache)

    def check_if_ok_to_update(self):
        """Check if it is ok to perform an http request."""
        current_time = int(time.time())
        last_refresh = self.last_refresh
        if last_refresh is None:
            last_refresh = 0
        if current_time >= (last_refresh + self.refresh_rate):
            self.last_refresh = current_time
            return True
        return False
