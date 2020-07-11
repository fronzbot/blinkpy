# -*- coding: utf-8 -*-
"""
blinkpy is an unofficial api for the Blink security camera system.

repo url: https://github.com/fronzbot/blinkpy

Original protocol hacking by MattTW :
https://github.com/MattTW/BlinkMonitorProtocol

Published under the MIT license - See LICENSE file for more details.
"Blink Wire-Free HS Home Monitoring & Alert Systems" is a trademark
owned by Immedia Inc., see www.blinkforhome.com for more information.
blinkpy is in no way affiliated with Blink, nor Immedia Inc.
"""

import os.path
import time
import logging
from shutil import copyfileobj

from requests.structures import CaseInsensitiveDict
from dateutil.parser import parse
from slugify import slugify

from blinkpy import api
from blinkpy.sync_module import BlinkSyncModule
from blinkpy.helpers.util import (
    create_session,
    merge_dicts,
    get_time,
    BlinkURLHandler,
    Throttle,
)
from blinkpy.helpers.constants import (
    BLINK_URL,
    DEFAULT_MOTION_INTERVAL,
    DEFAULT_REFRESH,
    MIN_THROTTLE_TIME,
    LOGIN_URLS,
)
from blinkpy.helpers.constants import __version__
from blinkpy.login_handler import LoginHandler


_LOGGER = logging.getLogger(__name__)


class Blink:
    """Class to initialize communication."""

    def __init__(
        self,
        username=None,
        password=None,
        cred_file=None,
        refresh_rate=DEFAULT_REFRESH,
        motion_interval=DEFAULT_MOTION_INTERVAL,
        legacy_subdomain=False,
        no_prompt=False,
        persist_key=None,
        device_id="Blinkpy",
    ):
        """
        Initialize Blink system.

        :param username: Blink username (usually email address)
        :param password: Blink password
        :param cred_file: JSON formatted file to store credentials.
                          If username and password are given, file
                          is ignored.  Otherwise, username and password
                          are loaded from file.
        :param refresh_rate: Refresh rate of blink information.
                             Defaults to 15 (seconds)
        :param motion_interval: How far back to register motion in minutes.
                                Defaults to last refresh time.
                                Useful for preventing motion_detected property
                                from de-asserting too quickly.
        :param legacy_subdomain: Set to TRUE to use old 'rest.region'
                                 endpoints (only use if you are having
                                 api issues).
        :param no_prompt: Set to TRUE if using an implementation that needs to
                          suppress command-line output.
        :param persist_key: Location of persistant identifier.
        :param device_id: Identifier for the application.  Default is 'Blinkpy'.
                          This is used when logging in and should be changed to
                          fit the implementation (ie. "Home Assistant" in a
                          Home Assistant integration).
        """
        self.login_handler = LoginHandler(
            username=username,
            password=password,
            cred_file=cred_file,
            persist_key=persist_key,
            device_id=device_id,
        )
        self._token = None
        self._auth_header = None
        self._host = None
        self.account_id = None
        self.client_id = None
        self.network_ids = []
        self.urls = None
        self.sync = CaseInsensitiveDict({})
        self.region = None
        self.region_id = None
        self.last_refresh = None
        self.refresh_rate = refresh_rate
        self.session = create_session()
        self.networks = []
        self.cameras = CaseInsensitiveDict({})
        self.video_list = CaseInsensitiveDict({})
        self.login_url = LOGIN_URLS[0]
        self.login_urls = []
        self.motion_interval = motion_interval
        self.version = __version__
        self.legacy = legacy_subdomain
        self.no_prompt = no_prompt
        self.available = False
        self.key_required = False
        self.login_response = {}

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
        if not self.available:
            self.get_auth_token()

        if self.key_required and not self.no_prompt:
            email = self.login_handler.data["username"]
            key = input("Enter code sent to {}: ".format(email))
            result = self.login_handler.send_auth_key(self, key)
            self.key_required = not result
            self.setup_post_verify()
        elif not self.key_required:
            self.setup_post_verify()

    def setup_post_verify(self):
        """Initialize blink system after verification."""
        camera_list = self.get_cameras()
        networks = self.get_ids()
        for network_name, network_id in networks.items():
            if network_id not in camera_list.keys():
                camera_list[network_id] = {}
                _LOGGER.warning("No cameras found for %s", network_name)
            sync_module = BlinkSyncModule(
                self, network_name, network_id, camera_list[network_id]
            )
            sync_module.start()
            self.sync[network_name] = sync_module
            self.cameras = self.merge_cameras()
        self.available = self.refresh()
        self.key_required = False

    def login(self):
        """Perform server login. DEPRECATED."""
        _LOGGER.warning(
            "Method is deprecated and will be removed in a future version.  Please use the LoginHandler.login() method instead."
        )
        return self.login_handler.login(self)

    def get_auth_token(self, is_retry=False):
        """Retrieve the authentication token from Blink."""
        self.login_response = self.login_handler.login(self)
        if not self.login_response:
            self.available = False
            return False
        self.setup_params(self.login_response)
        if self.login_handler.check_key_required(self):
            self.key_required = True
        return self._auth_header

    def setup_params(self, response):
        """Retrieve blink parameters from login response."""
        self.login_url = self.login_handler.login_url
        ((self.region_id, self.region),) = response["region"].items()
        self._host = "{}.{}".format(self.region_id, BLINK_URL)
        self._token = response["authtoken"]["authtoken"]
        self._auth_header = {"TOKEN_AUTH": self._token}
        self.urls = BlinkURLHandler(self.region_id, legacy=self.legacy)
        self.networks = self.get_networks()
        self.client_id = response["client"]["id"]
        self.account_id = response["account"]["id"]

    def get_networks(self):
        """Get network information."""
        response = api.request_networks(self)
        try:
            return response["summary"]
        except KeyError:
            return None

    def get_ids(self):
        """Set the network ID and Account ID."""
        all_networks = []
        network_dict = {}
        for network, status in self.networks.items():
            if status["onboarded"]:
                all_networks.append("{}".format(network))
                network_dict[status["name"]] = network

        self.network_ids = all_networks
        return network_dict

    def get_cameras(self):
        """Retrieve a camera list for each onboarded network."""
        response = api.request_homescreen(self)
        try:
            all_cameras = {}
            for camera in response["cameras"]:
                camera_network = str(camera["network_id"])
                camera_name = camera["name"]
                camera_id = camera["id"]
                camera_info = {"name": camera_name, "id": camera_id}
                if camera_network not in all_cameras:
                    all_cameras[camera_network] = []

                all_cameras[camera_network].append(camera_info)
            return all_cameras
        except KeyError:
            _LOGGER.error("Initialization failue. Could not retrieve cameras.")
            return {}

    @Throttle(seconds=MIN_THROTTLE_TIME)
    def refresh(self, force_cache=False):
        """
        Perform a system refresh.

        :param force_cache: Force an update of the camera cache
        """
        if self.check_if_ok_to_update() or force_cache:
            for sync_name, sync_module in self.sync.items():
                _LOGGER.debug("Attempting refresh of sync %s", sync_name)
                sync_module.refresh(force_cache=force_cache)
            if not force_cache:
                # Prevents rapid clearing of motion detect property
                self.last_refresh = int(time.time())
            return True
        return False

    def check_if_ok_to_update(self):
        """Check if it is ok to perform an http request."""
        current_time = int(time.time())
        last_refresh = self.last_refresh
        if last_refresh is None:
            last_refresh = 0
        if current_time >= (last_refresh + self.refresh_rate):
            return True
        return False

    def merge_cameras(self):
        """Merge all sync camera dicts into one."""
        combined = CaseInsensitiveDict({})
        for sync in self.sync:
            combined = merge_dicts(combined, self.sync[sync].cameras)
        return combined

    def download_videos(self, path, since=None, camera="all", stop=10, debug=False):
        """
        Download all videos from server since specified time.

        :param path: Path to write files.  /path/<cameraname>_<recorddate>.mp4
        :param since: Date and time to get videos from.
                      Ex: "2018/07/28 12:33:00" to retrieve videos since
                           July 28th 2018 at 12:33:00
        :param camera: Camera name to retrieve.  Defaults to "all".
                       Use a list for multiple cameras.
        :param stop: Page to stop on (~25 items per page. Default page 10).
        :param debug: Set to TRUE to prevent downloading of items.
                      Instead of downloading, entries will be printed to log.
        """
        if since is None:
            since_epochs = self.last_refresh
        else:
            parsed_datetime = parse(since, fuzzy=True)
            since_epochs = parsed_datetime.timestamp()

        formatted_date = get_time(time_to_convert=since_epochs)
        _LOGGER.info("Retrieving videos since %s", formatted_date)

        if not isinstance(camera, list):
            camera = [camera]

        for page in range(1, stop):
            response = api.request_videos(self, time=since_epochs, page=page)
            _LOGGER.debug("Processing page %s", page)
            try:
                result = response["media"]
                if not result:
                    raise IndexError
            except (KeyError, IndexError):
                _LOGGER.info("No videos found on page %s. Exiting.", page)
                break

            self._parse_downloaded_items(result, camera, path, debug)

    def _parse_downloaded_items(self, result, camera, path, debug):
        """Parse downloaded videos."""
        for item in result:
            try:
                created_at = item["created_at"]
                camera_name = item["device_name"]
                is_deleted = item["deleted"]
                address = item["media"]
            except KeyError:
                _LOGGER.info("Missing clip information, skipping...")
                continue

            if camera_name not in camera and "all" not in camera:
                _LOGGER.debug("Skipping videos for %s.", camera_name)
                continue

            if is_deleted:
                _LOGGER.debug("%s: %s is marked as deleted.", camera_name, address)
                continue

            clip_address = "{}{}".format(self.urls.base_url, address)
            filename = "{}-{}".format(camera_name, created_at)
            filename = "{}.mp4".format(slugify(filename))
            filename = os.path.join(path, filename)

            if not debug:
                if os.path.isfile(filename):
                    _LOGGER.info("%s already exists, skipping...", filename)
                    continue

                response = api.http_get(self, url=clip_address, stream=True, json=False)
                with open(filename, "wb") as vidfile:
                    copyfileobj(response.raw, vidfile)

                _LOGGER.info("Downloaded video to %s", filename)
            else:
                print(
                    ("Camera: {}, Timestamp: {}, " "Address: {}, Filename: {}").format(
                        camera_name, created_at, address, filename
                    )
                )
