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
import datetime
import aiofiles
import aiofiles.ospath
from requests.structures import CaseInsensitiveDict
from dateutil.parser import parse
from slugify import slugify

from blinkpy import api
from blinkpy.sync_module import BlinkSyncModule, BlinkOwl, BlinkLotus
from blinkpy.helpers import util
from blinkpy.helpers.constants import (
    DEFAULT_MOTION_INTERVAL,
    DEFAULT_REFRESH,
    MIN_THROTTLE_TIME,
    TIMEOUT_MEDIA,
)
from blinkpy.helpers.constants import __version__
from blinkpy.auth import Auth, BlinkTwoFARequiredError, TokenRefreshFailed, LoginError

_LOGGER = logging.getLogger(__name__)


class Blink:
    """Class to initialize communication."""

    def __init__(
        self,
        refresh_rate=DEFAULT_REFRESH,
        motion_interval=DEFAULT_MOTION_INTERVAL,
        no_owls=False,
        session=None,
    ):
        """
        Initialize Blink system.

        :param refresh_rate: Refresh rate of blink information.
                             Defaults to 30 (seconds)
        :param motion_interval: How far back to register motion in minutes.
                                Defaults to last refresh time.
                                Useful for preventing motion_detected property
                                from de-asserting too quickly.
        :param no_owls: Disable searching for owl entries (blink mini cameras \
                        only known entity).  Prevents an unnecessary API call \
                        if you don't have these in your network.
        """
        self.auth = Auth(session=session)
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
        self.homescreen = {}
        self.no_owls = no_owls

    @property
    def client_id(self):
        """Return the client id."""
        return self.auth.client_id

    @property
    def user_id(self):
        """Return the user id."""
        return self.auth.user_id

    @property
    def account_id(self):
        """Return the account id."""
        return self.auth.account_id

    async def prompt_2fa(self):
        """Prompt user for two-factor authentication code."""
        code = input("Enter the two-factor authentication code: ")
        await self.send_2fa_code(code)

    async def send_2fa_code(self, code):
        """Send the two-factor authentication code to complete login."""
        self.auth.data["2fa_code"] = code
        await self.start()

    @util.Throttle(seconds=MIN_THROTTLE_TIME)
    async def refresh(self, force=False, force_cache=False):
        """
        Perform a system refresh.

        :param force: Used to override throttle, resets refresh
        :param force_cache: Used to force update without overriding throttle
        """
        if force or force_cache or self.check_if_ok_to_update():
            if not self.available:
                await self.setup_post_verify()

            await self.get_homescreen()

            for sync_name, sync_module in self.sync.items():
                _LOGGER.debug("Attempting refresh of blink.sync['%s']", sync_name)
                await sync_module.refresh(force_cache=(force or force_cache))

            if not force_cache:
                # Prevents rapid clearing of motion detect property
                self.last_refresh = int(time.time())
                last_refresh = datetime.datetime.fromtimestamp(self.last_refresh)
                _LOGGER.debug("last_refresh = %s", last_refresh)

            return True
        return False

    async def start(self):
        """Perform full system setup."""
        try:
            await self.auth.startup()
            self.setup_urls()
            await self.get_homescreen()
        except (LoginError, TokenRefreshFailed, BlinkSetupError):
            _LOGGER.error("Cannot setup Blink platform.")
            self.available = False
            return False
        except BlinkTwoFARequiredError:
            raise

        if not self.last_refresh:
            # Initialize last_refresh to be just before the refresh delay period.
            self.last_refresh = int(time.time() - self.refresh_rate * 1.05)
            _LOGGER.debug(
                "Initialized last_refresh to %s == %s",
                self.last_refresh,
                datetime.datetime.fromtimestamp(self.last_refresh),
            )

        return await self.setup_post_verify()

    async def setup_post_verify(self):
        """Initialize blink system after verification."""
        try:
            if not self.homescreen:
                await self.get_homescreen()
            await self.setup_networks()
            networks = self.setup_network_ids()
            cameras = await self.setup_camera_list()
        except BlinkSetupError:
            self.available = False
            return False

        for name, network_id in networks.items():
            sync_cameras = cameras.get(network_id, {})
            await self.setup_sync_module(name, network_id, sync_cameras)

        self.cameras = self.merge_cameras()

        self.available = True
        return True

    async def setup_sync_module(self, name, network_id, cameras):
        """Initialize a sync module."""
        self.sync[name] = BlinkSyncModule(self, name, network_id, cameras)
        await self.sync[name].start()

    async def get_homescreen(self):
        """Get homescreen information."""
        if self.no_owls:
            _LOGGER.debug("Skipping owl extraction.")
            self.homescreen = {}
            return
        res = await api.request_homescreen(self)
        await self.validate_homescreen(res)
        _LOGGER.debug("homescreen = %s", util.json_dumps(self.homescreen))

    async def validate_homescreen(self, response):
        """Validate and process homescreen response data."""
        self.homescreen = await response.json()
        self.auth.client_id = response.headers.get("Client-Id")
        self.auth.user_id = response.headers.get("User-Id")

    async def setup_owls(self):
        """Check for mini cameras."""
        network_list = []
        camera_list = []
        try:
            for owl in self.homescreen["owls"]:
                name = owl["name"]
                network_id = str(owl["network_id"])
                if network_id in self.network_ids:
                    camera_list.append(
                        {network_id: {"name": name, "id": network_id, "type": "mini"}}
                    )
                    continue
                if owl["onboarded"]:
                    network_list.append(str(network_id))
                    self.sync[name] = BlinkOwl(self, name, network_id, owl)
                    await self.sync[name].start()
        except (KeyError, TypeError):
            # No sync-less devices found
            pass

        self.network_ids.extend(network_list)
        return camera_list

    async def setup_lotus(self):
        """Check for doorbells cameras."""
        network_list = []
        camera_list = []
        try:
            for lotus in self.homescreen["doorbells"]:
                name = lotus["name"]
                network_id = str(lotus["network_id"])
                if network_id in self.network_ids:
                    camera_list.append(
                        {
                            network_id: {
                                "name": name,
                                "id": network_id,
                                "type": "doorbell",
                            }
                        }
                    )
                    continue
                if lotus["onboarded"]:
                    network_list.append(str(network_id))
                    self.sync[name] = BlinkLotus(self, name, network_id, lotus)
                    await self.sync[name].start()
        except (KeyError, TypeError):
            # No sync-less devices found
            pass

        self.network_ids.extend(network_list)
        return camera_list

    async def setup_camera_list(self):
        """Create camera list for onboarded networks."""
        all_cameras = {}
        response = await api.request_camera_usage(self)
        try:
            for network in response["networks"]:
                _LOGGER.info("network = %s", util.json_dumps(network))
                camera_network = str(network["network_id"])
                if camera_network not in all_cameras:
                    all_cameras[camera_network] = []
                for camera in network["cameras"]:
                    all_cameras[camera_network].append(
                        {"name": camera["name"], "id": camera["id"], "type": "default"}
                    )
            mini_cameras = await self.setup_owls()
            lotus_cameras = await self.setup_lotus()
            for camera in mini_cameras:
                for network, camera_info in camera.items():
                    all_cameras[network].append(camera_info)
            for camera in lotus_cameras:
                for network, camera_info in camera.items():
                    all_cameras[network].append(camera_info)
            return all_cameras
        except (KeyError, TypeError) as ex:
            _LOGGER.error("Unable to retrieve cameras from response %s", response)
            raise BlinkSetupError from ex

    def setup_urls(self):
        """Create urls for api."""
        try:
            self.urls = util.BlinkURLHandler(self.auth.region_id)
        except TypeError as ex:
            _LOGGER.error(
                "Unable to extract region is from response %s", self.auth.tier_info
            )
            raise BlinkSetupError from ex

    async def setup_networks(self):
        """Get network information."""
        response = await api.request_networks(self)
        try:
            self.networks = response["summary"]
        except (KeyError, TypeError) as ex:
            raise BlinkSetupError from ex

    def setup_network_ids(self):
        """Create the network ids for onboarded networks."""
        all_networks = []
        network_dict = {}
        try:
            for network, status in self.networks.items():
                if status["onboarded"]:
                    all_networks.append(f"{network}")
                    network_dict[status["name"]] = network
        except AttributeError as ex:
            _LOGGER.error(
                "Unable to retrieve network information from %s", self.networks
            )
            raise BlinkSetupError from ex

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

    async def save(self, file_name):
        """Save login data to file."""
        await util.json_save(self.auth.login_attributes, file_name)

    async def get_status(self):
        """Get the blink system notification status."""
        response = await api.request_notification_flags(self)
        return response.get("notifications", response)

    async def set_status(self, data_dict={}):
        """
        Set the blink system notification status.

        :param data_dict: Dictionary of notification keys to modify.
                          Example: {'low_battery': False, 'motion': False}
        """
        response = await api.request_set_notification_flag(self, data_dict)
        return response

    async def download_videos(
        self, path, since=None, camera="all", stop=10, delay=1, debug=False
    ):
        """
        Download all videos from server since specified time.

        :param path: Path to write files.  /path/<cameraname>_<recorddate>.mp4
        :param since: Date and time to get videos from.
                      Ex: "2018/07/28 12:33:00" to retrieve videos since
                      July 28th 2018 at 12:33:00
        :param camera: Camera name to retrieve.  Defaults to "all".
                       Use a list for multiple cameras.
        :param stop: Page to stop on (~25 items per page. Default page 10).
        :param delay: Number of seconds to wait in between subsequent video downloads.
        :param debug: Set to TRUE to prevent downloading of items.
                      Instead of downloading, entries will be printed to log.
        """
        if not isinstance(camera, list):
            camera = [camera]

        results = await self.get_videos_metadata(since=since, stop=stop)
        await self._parse_downloaded_items(results, camera, path, delay, debug)

    async def get_videos_metadata(self, since=None, camera="all", stop=10):
        """
        Fetch and return video metadata.

        :param since: Date and time to get videos from.
                      Ex: "2018/07/28 12:33:00" to retrieve videos since
                      July 28th 2018 at 12:33:00
        :param stop: Page to stop on (~25 items per page. Default page 10).
        """
        videos = []
        if since is None:
            since_epochs = self.last_refresh
        else:
            parsed_datetime = parse(since, fuzzy=True)
            since_epochs = parsed_datetime.timestamp()

        formatted_date = util.get_time(time_to_convert=since_epochs)
        _LOGGER.info("Retrieving videos since %s", formatted_date)

        for page in range(1, stop):
            response = await api.request_videos(self, time=since_epochs, page=page)
            _LOGGER.debug("Processing page %s", page)
            try:
                result = response["media"]
                if not result:
                    raise KeyError
                videos.extend(result)
            except (KeyError, TypeError):
                _LOGGER.info("No videos found on page %s. Exiting.", page)
                break
        return videos

    async def do_http_get(self, address):
        """
        Do an http_get on address.

        :param address: address to be added to base_url.
        """
        response = await api.http_get(
            self,
            url=f"{self.urls.base_url}{address}",
            stream=True,
            json=False,
            timeout=TIMEOUT_MEDIA,
        )
        return response

    async def _parse_downloaded_items(self, result, camera, path, delay, debug):
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

            filename = f"{camera_name}-{created_at}"
            filename = f"{slugify(filename)}.mp4"
            filename = os.path.join(path, filename)

            if not debug:
                if await aiofiles.ospath.isfile(filename):
                    _LOGGER.info("%s already exists, skipping...", filename)
                    continue

                response = await self.do_http_get(address)
                async with aiofiles.open(filename, "wb") as vidfile:
                    await vidfile.write(await response.read())

                _LOGGER.info("Downloaded video to %s", filename)
            else:
                print(
                    f"Camera: {camera_name}, Timestamp: {created_at}, "
                    f"Address: {address}, Filename: {filename}"
                )
            if delay > 0:
                time.sleep(delay)


class BlinkSetupError(Exception):
    """Class to handle setup errors."""
