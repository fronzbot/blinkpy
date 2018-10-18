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
import getpass
import logging
import blinkpy.helpers.errors as ERROR
from blinkpy import api
from blinkpy.sync_module import BlinkSyncModule
from blinkpy.helpers.util import (
    create_session, BlinkURLHandler,
    BlinkAuthenticationException)
from blinkpy.helpers.constants import (
    BLINK_URL, LOGIN_URL, LOGIN_BACKUP_URL, PROJECT_URL)

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
        self.network_id = None
        self.account_id = None
        self.urls = None
        self.sync = None
        self.region = None
        self.region_id = None
        self.last_refresh = None
        self.refresh_rate = refresh_rate
        self.session = None
        self.networks = []
        self._login_url = LOGIN_URL

    @property
    def auth_header(self):
        """Return the authentication header."""
        return self._auth_header

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
        self.sync = BlinkSyncModule(self)
        self.sync.start()

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

        login_url = LOGIN_URL
        self.session = create_session()
        response = api.request_login(self,
                                     login_url,
                                     self._username,
                                     self._password)

        if response.status_code == 200:
            response = response.json()
            (self.region_id, self.region), = response['region'].items()
        else:
            _LOGGER.debug(
                ("Received response code %s "
                 "when authenticating, "
                 "trying new url"), response.status_code
            )
            login_url = LOGIN_BACKUP_URL
            response = api.request_login(self,
                                         login_url,
                                         self._username,
                                         self._password)
            self.region_id = 'piri'
            self.region = "UNKNOWN"

        self._host = "{}.{}".format(self.region_id, BLINK_URL)
        self._token = response['authtoken']['authtoken']
        self._auth_header = {'Host': self._host,
                             'TOKEN_AUTH': self._token}
        self.networks = response['networks']
        self.urls = BlinkURLHandler(self.region_id)
        self._login_url = login_url

        return self._auth_header

    def get_ids(self):
        """Set the network ID and Account ID."""
        response = api.request_networks(self)
        # Look for only onboarded network, flag warning if multiple
        # since it's unexpected
        all_networks = []
        for network, status in self.networks.items():
            if status['onboarded']:
                all_networks.append(network)
        self.network_id = all_networks.pop(0)
        for resp in response['networks']:
            if str(resp['id']) == self.network_id:
                self.account_id = resp['account_id']
        if all_networks:
            _LOGGER.error(("More than one unboarded network. "
                           "Platform may not work as intended. "
                           "Please open an issue on %s"), PROJECT_URL)

    def refresh(self, force_cache=False):
        """
        Perform a system refresh.

        :param force_cache: Force an update of the camera cache
        """
        if self.check_if_ok_to_update() or force_cache:
            _LOGGER.debug("Attempting refresh of cameras.")
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
