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
from blinkpy.sync_module import BlinkSyncModule, BlinkOwl
from blinkpy.helpers import util
from blinkpy.helpers.constants import (
    DEFAULT_MOTION_INTERVAL,
    DEFAULT_REFRESH,
    MIN_THROTTLE_TIME,
)
from blinkpy.helpers.constants import __version__
from blinkpy.auth import Auth, TokenRefreshFailed, LoginError

_LOGGER = logging.getLogger(__name__)


class Blink:
    """Class to initialize communication."""

    def __init__(
        self, refresh_rate=DEFAULT_REFRESH, motion_interval=DEFAULT_MOTION_INTERVAL,
    ):
        """
        Initialize Blink system.

        :param refresh_rate: Refresh rate of blink information.
                             Defaults to 15 (seconds)
        :param motion_interval: How far back to register motion in minutes.
                                Defaults to last refresh time.
                                Useful for preventing motion_detected property
                                from de-asserting too quickly.
        """
        self.auth = Auth()
        self.account_id = None
        self.client_id = None
        self.network_ids = []
        self.urls = None
        self.sync = CaseInsensitiveDict({})
        self.last_refresh = None
        self.refresh_rate = refresh_rate
        self.networks = []
        self.cameras = CaseInsensitiveDict({})
        self.video_list = CaseInsensitiveDict({})
        self.motion_interval = motion_interval
        self.version = __version__
        self.available = False
        self.key_required = False
        self.homescreen = {}

    @util.Throttle(seconds=MIN_THROTTLE_TIME)
    def refresh(self, force=False):
        """
        Perform a system refresh.

        :param force: Force an update of the camera data
        """
        if self.check_if_ok_to_update() or force:
            if not self.available:
                self.setup_post_verify()

            for sync_name, sync_module in self.sync.items():
                _LOGGER.debug("Attempting refresh of sync %s", sync_name)
                sync_module.refresh(force_cache=force)
            if not force:
                # Prevents rapid clearing of motion detect property
                self.last_refresh = int(time.time())
            return True
        return False

    def start(self):
        """Perform full system setup."""
        try:
            self.auth.startup()
            self.setup_login_ids()
            self.setup_urls()
        except (LoginError, TokenRefreshFailed, BlinkSetupError):
            _LOGGER.error("Cannot setup Blink platform.")
            self.available = False
            return False

        self.key_required = self.auth.check_key_required()
        if self.key_required:
            if self.auth.no_prompt:
                return True
            self.setup_prompt_2fa()
        return self.setup_post_verify()

    def setup_prompt_2fa(self):
        """Prompt for 2FA."""
        email = self.auth.data["username"]
        pin = input(f"Enter code sent to {email}: ")
        result = self.auth.send_auth_key(self, pin)
        self.key_required = not result

    def setup_post_verify(self):
        """Initialize blink system after verification."""
        try:
            self.setup_networks()
            networks = self.setup_network_ids()
            cameras = self.setup_camera_list()
        except BlinkSetupError:
            self.available = False
            return False

        for name, network_id in networks.items():
            sync_cameras = cameras.get(network_id, {})
            self.setup_sync_module(name, network_id, sync_cameras)

        self.setup_owls()
        self.cameras = self.merge_cameras()

        self.available = True
        self.key_required = False
        return True

    def setup_sync_module(self, name, network_id, cameras):
        """Initialize a sync module."""
        self.sync[name] = BlinkSyncModule(self, name, network_id, cameras)
        self.sync[name].start()

    def setup_owls(self):
        """Check for mini cameras."""
        response = api.request_homescreen(self)
        self.homescreen = response
        network_list = []
        try:
            for owl in response["owls"]:
                name = owl["name"]
                network_id = owl["network_id"]
                if owl["onboarded"]:
                    network_list.append(str(network_id))
                    self.sync[name] = BlinkOwl(self, name, network_id, owl)
                    self.sync[name].start()
        except KeyError:
            # No sync-less devices found
            pass

        self.network_ids.extend(network_list)

    def setup_camera_list(self):
        """Create camera list for onboarded networks."""
        all_cameras = {}
        response = api.request_camera_usage(self)
        try:
            for network in response["networks"]:
                camera_network = str(network["network_id"])
                if camera_network not in all_cameras:
                    all_cameras[camera_network] = []
                for camera in network["cameras"]:
                    all_cameras[camera_network].append(
                        {"name": camera["name"], "id": camera["id"]}
                    )
            return all_cameras
        except (KeyError, TypeError):
            _LOGGER.error("Unable to retrieve cameras from response %s", response)
            raise BlinkSetupError

    def setup_login_ids(self):
        """Retrieve login id numbers from login response."""
        self.client_id = self.auth.client_id
        self.account_id = self.auth.account_id

    def setup_urls(self):
        """Create urls for api."""
        try:
            self.urls = util.BlinkURLHandler(self.auth.region_id)
        except TypeError:
            _LOGGER.error(
                "Unable to extract region is from response %s", self.auth.login_response
            )
            raise BlinkSetupError

    def setup_networks(self):
        """Get network information."""
        response = api.request_networks(self)
        try:
            self.networks = response["summary"]
        except (KeyError, TypeError):
            raise BlinkSetupError

    def setup_network_ids(self):
        """Create the network ids for onboarded networks."""
        all_networks = []
        network_dict = {}
        try:
            for network, status in self.networks.items():
                if status["onboarded"]:
                    all_networks.append(f"{network}")
                    network_dict[status["name"]] = network
        except AttributeError:
            _LOGGER.error(
                "Unable to retrieve network information from %s", self.networks
            )
            raise BlinkSetupError

        self.network_ids = all_networks
        return network_dict

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
            combined = util.merge_dicts(combined, self.sync[sync].cameras)
        return combined

    def save(self, file_name):
        """Save login data to file."""
        util.json_save(self.auth.login_attributes, file_name)

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

        formatted_date = util.get_time(time_to_convert=since_epochs)
        _LOGGER.info("Retrieving videos since %s", formatted_date)

        if not isinstance(camera, list):
            camera = [camera]

        for page in range(1, stop):
            response = api.request_videos(self, time=since_epochs, page=page)
            _LOGGER.debug("Processing page %s", page)
            try:
                result = response["media"]
                if not result:
                    raise KeyError
            except (KeyError, TypeError):
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

            clip_address = f"{self.urls.base_url}{address}"
            filename = f"{camera_name}-{created_at}"
            filename = f"{slugify(filename)}.mp4"
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
                    (
                        f"Camera: {camera_name}, Timestamp: {created_at}, "
                        "Address: {address}, Filename: {filename}"
                    )
                )


class BlinkSetupError(Exception):
    """Class to handle setup errors."""
