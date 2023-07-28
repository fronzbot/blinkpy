"""Defines a sync module for Blink."""
from __future__ import annotations
from typing import TYPE_CHECKING
import logging
import string
import datetime
import traceback
import asyncio
from sortedcontainers import SortedSet #type: ignore
from requests.structures import CaseInsensitiveDict
from blinkpy import api
from blinkpy.camera import BlinkCamera, BlinkCameraMini, BlinkDoorbell
from blinkpy.helpers.util import time_to_seconds, backoff_seconds, to_alphanumeric
from blinkpy.helpers.constants import ONLINE

if TYPE_CHECKING:
    from blinkpy.blinkpy import Blink
    from blinkpy.helpers.util import BlinkURLHandler
    from aiohttp import ClientResponse

_LOGGER = logging.getLogger(__name__)


class BlinkSyncModule:
    """Class to initialize sync module."""

    def __init__(
        self, blink: Blink, network_name: str, network_id: str, camera_list: list
    ) -> None:
        """
        Initialize Blink sync module.

        :param blink: Blink class instantiation
        """
        self.blink = blink
        self.network_id = network_id
        self.region_id = blink.auth.region_id
        self.name: str = network_name
        self.serial: str = ""
        self.status = "offline"
        self.sync_id: str = ""
        self.host: str = ""
        self.summary: dict = {}
        self.network_info: dict = {}
        self.events: list = []
        self.cameras: CaseInsensitiveDict = CaseInsensitiveDict({})
        self.motion_interval: int = blink.motion_interval
        self.motion: dict = {}
        # A dictionary where keys are the camera names, and values are lists of recent clips.
        self.last_records: dict = {}
        self.camera_list: list = camera_list
        self.available: bool = False
        self.type_key_map: dict = {
            "mini": "owls",
            "doorbell": "doorbells",
        }
        self._names_table: dict = {}
        self._local_storage: dict = {
            "enabled": False,
            "compatible": False,
            "status": False,
            "last_manifest_id": None,
            "manifest": SortedSet(),
            "manifest_stale": True,
            "last_manifest_read": datetime.datetime(1970, 1, 1, 0, 0, 0).isoformat(),
        }

    @property
    def attributes(self) -> dict:
        """Return sync attributes."""
        attr = {
            "name": self.name,
            "id": self.sync_id,
            "network_id": self.network_id,
            "serial": self.serial,
            "status": self.status,
            "region_id": self.region_id,
            "local_storage": self.local_storage,
        }
        return attr

    @property
    def urls(self) -> BlinkURLHandler:
        """Return device urls."""
        return self.blink.urls

    @property
    def online(self) -> bool:
        """Return boolean system online status."""
        try:
            return ONLINE[self.status]
        except KeyError:
            _LOGGER.error("Unknown sync module status %s", self.status)
            self.available = False
            return False

    @property
    def arm(self) -> bool | None:
        """Return status of sync module: armed/disarmed."""
        try:
            return self.network_info["network"]["armed"]
        except (KeyError, TypeError):
            self.available = False
            return None

    @property
    def local_storage(self) -> str:
        """Indicate if local storage is activated or not (True/False)."""
        return self._local_storage["status"]

    @property
    def local_storage_manifest_ready(self) -> bool:
        """Indicate if the manifest is up-to-date."""
        return not self._local_storage["manifest_stale"]

    async def async_arm(self, value: bool) -> ClientResponse:
        """Arm or disarm camera."""
        if value:
            return await api.request_system_arm(self.blink, self.network_id)
        return await api.request_system_disarm(self.blink, self.network_id)

    async def start(self) -> bool:
        """Initialize the system."""
        _LOGGER.debug("Initializing the sync module")
        response = await self.sync_initialize()
        if not response:
            return False

        try:
            self.sync_id = self.summary["id"] # type: ignore
            self.serial = self.summary["serial"] # type: ignore
            self.status = self.summary["status"] # type: ignore
        except KeyError:
            _LOGGER.error("Could not extract some sync module info: %s", response)

        is_ok = await self.get_network_info()

        if not is_ok or not await self.update_cameras():
            self.available = False
            return False
        self.available = True
        return True

    async def sync_initialize(self) -> dict | bool:
        """Initialize a sync module."""
        # Doesn't include local store info for some reason.
        response = await api.request_syncmodule(self.blink, self.network_id)
        try:
            self.summary: dict = response["syncmodule"] # type: ignore
            self.network_id = self.summary["network_id"] # type: ignore
            await self._init_local_storage(self.summary["id"])
        except (TypeError, KeyError):
            _LOGGER.error(
                "Could not retrieve sync module information with response: %s", response
            )
            return False
        if isinstance(response,dict):
            return response
        return False

    async def _init_local_storage(self, sync_id: str) -> dict | bool:
        """Initialize local storage from homescreen dictionary."""
        home_screen = self.blink.homescreen
        sync_module: dict = {}
        try:
            sync_modules = home_screen["sync_modules"]
            for mod in sync_modules:
                if mod["id"] == sync_id:
                    self._local_storage["enabled"] = mod["local_storage_enabled"]
                    self._local_storage["compatible"] = mod["local_storage_compatible"]
                    self._local_storage["status"] = (
                        mod["local_storage_status"] == "active"
                    )
                    self._local_storage["last_manifest_read"] = (
                        datetime.datetime.utcnow() - datetime.timedelta(seconds=10)
                    ).isoformat()
                    sync_module = mod
        except (TypeError, KeyError):
            _LOGGER.error(
                "Could not retrieve sync module information from home screen: %s",
                home_screen,
            )
            return False
        return sync_module

    async def update_cameras(self, camera_type = BlinkCamera) -> bool:
        """Update cameras from server."""
        type_map = {
            "mini": BlinkCameraMini,
            "doorbell": BlinkDoorbell,
            "default": BlinkCamera,
        }
        try:
            _LOGGER.debug("Updating cameras")
            for camera_config in self.camera_list:
                if "name" not in camera_config:
                    break
                blink_camera_type = camera_config.get("type", "")
                name = camera_config["name"]
                self.motion[name] = False
                unique_info = self.get_unique_info(name)
                if blink_camera_type in type_map:
                    camera_type = type_map.get(blink_camera_type,None)
                self.cameras[name] = camera_type(self)
                camera_info = await self.get_camera_info(
                    camera_config["id"], unique_info=unique_info
                )
                self._names_table[to_alphanumeric(name)] = name
                await self.cameras[name].update(
                    camera_info, force_cache=True, force=True
                )
        except KeyError:
            _LOGGER.error("Could not create camera instances for %s", self.name)
            return False
        return True

    def get_unique_info(self, name: str) -> dict | None:
        """Extract unique information for Minis and Doorbells."""
        try:
            for camera_type in self.type_key_map:
                type_key = self.type_key_map[camera_type]
                for device in self.blink.homescreen[type_key]:
                    if device["name"] == name:
                        return device
        except (TypeError, KeyError):
            pass
        return None

    async def get_events(self, **kwargs) -> dict | bool:
        """Retrieve events from server."""
        kwargs.pop("force", False)
        response = await api.request_sync_events(self.blink, self.network_id)
        try:
            return response["event"]
        except (TypeError, KeyError):
            _LOGGER.error("Could not extract events: %s", response)
            return False

    async def get_camera_info(self, camera_id: str, **kwargs) -> dict:
        """Retrieve camera information."""
        unique = kwargs.get("unique_info", None)
        if unique is not None:
            return unique
        response = await api.request_camera_info(self.blink, self.network_id, camera_id)
        try:
            return response["camera"][0] #type: ignore
        except (TypeError, KeyError):
            _LOGGER.error(
                "Could not extract camera info for %s: %s", camera_id, response
            )
            return {}

    async def get_network_info(self) -> bool:
        """Retrieve network status."""
        response =  await api.request_network_update(
            self.blink, self.network_id
        )
        if isinstance(response,dict):
            self.network_info = response
        try:
            if self.network_info["network"]["sync_module_error"]:
                raise KeyError
        except (TypeError, KeyError):
            self.available = False
            return False
        return True

    async def refresh(self, force_cache: bool = False) -> None:
        """Get all blink cameras and pulls their most recent status."""
        if not await self.get_network_info():
            return
        await self.update_local_storage_manifest()
        await self.check_new_videos()
        for camera_name in self.cameras:
            camera_id = self.cameras[camera_name].camera_id
            camera_info = await self.get_camera_info(
                camera_id,
                unique_info=self.get_unique_info(camera_name),
            )
            await self.cameras[camera_name].update(camera_info, force_cache=force_cache)
        self.available = True

    async def check_new_videos(self) -> bool:
        """Check if new videos since last refresh."""
        _LOGGER.debug("Checking for new videos")
        try:
            interval = self.blink.last_refresh - self.motion_interval * 60 # type: ignore
            last_refresh = datetime.datetime.fromtimestamp(self.blink.last_refresh)
            _LOGGER.debug(f"last_refresh = {last_refresh}")
            _LOGGER.debug(f"interval={interval}")
        except TypeError:
            # This is the first start, so refresh hasn't happened yet.
            # No need to check for motion.
            ex = traceback.format_exc()
            _LOGGER.error(
                f"Error calculating interval (last_refresh={self.blink.last_refresh}): {ex}"
            )
            trace = "".join(traceback.format_stack())
            _LOGGER.debug(f"\n{trace}")
            _LOGGER.info("No new videos since last refresh.")
            return False

        resp = await api.request_videos(self.blink, time=interval, page=1)

        last_record = {}
        for camera in self.cameras.keys():
            # Initialize the list if doesn't exist yet.
            if camera not in self.last_records:
                self.last_records[camera] = []
            # Hang on to the last record if there is one.
            if len(self.last_records[camera]) > 0:
                last_record[camera] = self.last_records[camera][-1]
            # Reset in preparation for processing new entries.
            self.last_records[camera] = []
            self.motion[camera] = False

        try:
            info = resp["media"] # type: ignore
        except (KeyError, TypeError):
            _LOGGER.warning("Could not check for motion. Response: %s", resp)
            return False

        for entry in info:
            try:
                name = entry["device_name"]
                clip_url = entry["media"]
                timestamp = entry["created_at"]
                if self.check_new_video_time(timestamp):
                    self.motion[name] = True and self.arm
                    record = {"clip": clip_url, "time": timestamp}
                    self.last_records[name].append(record)
            except KeyError:
                last_refresh = datetime.datetime.fromtimestamp(self.blink.last_refresh)
                _LOGGER.debug(
                    f"No new videos for {entry} since last refresh at {last_refresh}."
                )

        # Process local storage if active and if the manifest is ready.
        last_manifest_read_local = datetime.datetime.fromisoformat(
            self._local_storage["last_manifest_read"]
        )
        _LOGGER.debug(f"last_manifest_read = {last_manifest_read_local}")
        _LOGGER.debug(f"Manifest ready? {self.local_storage_manifest_ready}")
        if self.local_storage and self.local_storage_manifest_ready:
            _LOGGER.debug("Processing updated manifest")
            manifest = self._local_storage["manifest"]
            last_manifest_id = self._local_storage["last_manifest_id"]
            last_manifest_read = self._local_storage["last_manifest_read"]
            last_read_local = (
                datetime.datetime.fromisoformat(last_manifest_read)
                .replace(tzinfo=datetime.timezone.utc)
                .astimezone(tz=None)
            )
            last_clip_time = None
            num_new = 0
            for item in reversed(manifest):
                iso_timestamp = item.created_at.isoformat()

                _LOGGER.debug(
                    f"Checking '{item.name}': clip_time={iso_timestamp}, manifest_read={last_manifest_read}"
                )
                # Exit the loop once there are no new videos in the list.
                if not self.check_new_video_time(iso_timestamp, last_manifest_read):
                    _LOGGER.info(
                        f"No new local storage videos since last manifest read at {last_read_local}."
                    )
                    break
                _LOGGER.debug(f"Found new item in local storage manifest: {item}")
                name = item.name
                clip_url = item.url(last_manifest_id)
                await item.prepare_download(self.blink)
                self.motion[name] = True
                record = {"clip": clip_url, "time": iso_timestamp}
                self.last_records[name].append(record)
                last_clip_time = item.created_at
                num_new += 1

            # The manifest became ready, and we read recent clips from it.
            if num_new > 0:
                last_manifest_read = (
                    datetime.datetime.utcnow() - datetime.timedelta(seconds=10)
                ).isoformat()
                self._local_storage["last_manifest_read"] = last_manifest_read
                _LOGGER.debug(f"Updated last_manifest_read to {last_manifest_read}")
                _LOGGER.debug(f"Last clip time was {last_clip_time}")

        # We want to keep the last record when no new motion was detected.
        for camera in self.cameras.keys():
            # Check if there are no new records, indicating motion.
            if len(self.last_records[camera]) == 0:
                # If no new records, check if we had a previous last record.
                if camera in last_record:
                    # Put the last record back into the empty list.
                    self.last_records[camera].append(last_record[camera])

        return True

    def check_new_video_time(self, timestamp: str, reference: str | None = None) -> bool:
        """Check if video has timestamp since last refresh."""
        """
        :param timestamp ISO-formatted timestamp string
        :param reference ISO-formatted reference timestamp string
        """
        if not reference:
            return time_to_seconds(timestamp) > self.blink.last_refresh
        return time_to_seconds(timestamp) > time_to_seconds(reference)

    async def update_local_storage_manifest(self) -> bool | None:
        """Update local storage manifest, which lists all stored clips."""
        if not self.local_storage:
            self._local_storage["manifest_stale"] = True
            return None
        _LOGGER.debug("Updating local storage manifest")

        response = await self.poll_local_storage_manifest()
        try:
            manifest_request_id = response["id"] #type: ignore
        except (TypeError, KeyError):
            _LOGGER.error(
                "Could not extract manifest request ID from response: %s", response
            )
            self._local_storage["manifest_stale"] = True
            return None

        response = await self.poll_local_storage_manifest(manifest_request_id)
        try:
            manifest_id = response["manifest_id"] #type: ignore
        except (TypeError, KeyError):
            _LOGGER.error("Could not extract manifest ID from response: %s", response)
            self._local_storage["manifest_stale"] = True
            return None

        self._local_storage["last_manifest_id"] = manifest_id
        template = string.Template(api.local_storage_clip_url_template()).substitute(
            account_id=self.blink.account_id,
            network_id=self.network_id,
            sync_id=self.sync_id,
            manifest_id="$manifest_id",
            clip_id="$clip_id",
        )
        num_stored = len(self._local_storage["manifest"])
        try:
            for item in response["clips"]: #type: ignore
                alphanumeric_name = item["camera_name"]
                if alphanumeric_name in self._names_table:
                    camera_name = self._names_table[alphanumeric_name]
                    self._local_storage["manifest"].add(
                        LocalStorageMediaItem(
                            item["id"],
                            camera_name,
                            item["created_at"],
                            item["size"],
                            manifest_id,
                            template,
                        )
                    )
            num_added = len(self._local_storage["manifest"]) - num_stored
            if num_added > 0:
                _LOGGER.info(
                    f"Found {num_added} new clip(s) in local storage manifest id={manifest_id}"
                )
        except (TypeError, KeyError):
            ex = traceback.format_exc()
            _LOGGER.error(f"Could not extract clips list from response: {ex}")
            trace = "".join(traceback.format_stack())
            _LOGGER.debug(f"\n{trace}")
            self._local_storage["manifest_stale"] = True
            return None

        self._local_storage["manifest_stale"] = False
        return True

    async def poll_local_storage_manifest(
        self, manifest_request_id: str | None = None, max_retries: int = 4
    ) -> dict:
        """Poll for local storage manifest."""
        # The sync module may be busy processing another request (like saving a new clip).
        # Poll the endpoint until it is ready, backing off each retry.
        response = None
        for retry in range(max_retries):
            # Request building the manifest.
            if not manifest_request_id:
                response = await api.request_local_storage_manifest(
                    self.blink, self.network_id, self.sync_id
                )
                if isinstance(response,dict) and "id" in response:
                    break
            # Get the manifest.
            else:
                response = await api.get_local_storage_manifest(
                    self.blink, self.network_id, self.sync_id, manifest_request_id
                )
                if isinstance(response,dict) and "clips" in response:
                    break
            seconds = backoff_seconds(retry=retry, default_time=3)
            _LOGGER.debug("[retry=%d] Retrying in %d seconds", retry + 1, seconds)
            await asyncio.sleep(seconds)
        if isinstance(response,dict):
            return response
        return {}


class BlinkOwl(BlinkSyncModule):
    """Representation of a sync-less device."""

    def __init__(
        self, blink: Blink, name: str, network_id: str, response: dict
    ) -> None:
        """Initialize a sync-less object."""
        cameras = [{"name": name, "id": response["id"]}]
        super().__init__(blink, name, network_id, cameras)
        self.sync_id = response["id"]
        self.serial = response["serial"]
        self.status = response["enabled"]
        if not self.serial:
            self.serial = f"{network_id}-{self.sync_id}"

    async def sync_initialize(self) -> dict | bool:
        """Initialize a sync-less module."""
        self.summary = {
            "id": self.sync_id,
            "name": self.name,
            "serial": self.serial,
            "status": self.status,
            "onboarded": True,
            "account_id": self.blink.account_id,
            "network_id": self.network_id,
        }
        return self.summary

    async def update_cameras(
        self, camera_type = BlinkCameraMini
    ) -> bool:
        """Update sync-less cameras."""
        return await super().update_cameras(camera_type=BlinkCameraMini)

    async def get_camera_info(self, camera_id: str, **kwargs) -> dict:
        """Retrieve camera information."""
        try:
            for owl in self.blink.homescreen["owls"]:
                if owl["name"] == self.name:
                    self.status = owl["enabled"]
                    return owl
        except (TypeError, KeyError):
            pass
        return {}

    async def get_network_info(self) -> bool:
        """Get network info for sync-less module."""
        return True

    @property
    def network_info(self) -> dict:
        """Format owl response to resemble sync module."""
        return {
            "network": {
                "id": self.network_id,
                "name": self.name,
                "armed": self.status,
                "sync_module_error": False,
                "account_id": self.blink.account_id,
            }
        }

    @network_info.setter
    def network_info(self, value: str):
        """Set network_info property."""


class BlinkLotus(BlinkSyncModule):
    """Representation of a sync-less device."""

    def __init__(
        self, blink: Blink, name: str, network_id: str, response: dict
    ) -> None:
        """Initialize a sync-less object."""
        cameras = [{"name": name, "id": response["id"]}]
        super().__init__(blink, name, network_id, cameras)
        self.sync_id = response["id"]
        self.serial = response["serial"]
        self.status = response["enabled"]
        if not self.serial:
            self.serial = f"{network_id}-{self.sync_id}"

    async def sync_initialize(self) -> dict | bool:
        """Initialize a sync-less module."""
        self.summary = {
            "id": self.sync_id,
            "name": self.name,
            "serial": self.serial,
            "status": self.status,
            "onboarded": True,
            "account_id": self.blink.account_id,
            "network_id": self.network_id,
        }
        return self.summary

    async def update_cameras(self, camera_type = BlinkDoorbell) -> bool:
        """Update sync-less cameras."""
        return await super().update_cameras(camera_type=BlinkDoorbell)

    async def get_camera_info(self, camera_id: str, **kwargs) -> dict:
        """Retrieve camera information."""
        try:
            for doorbell in self.blink.homescreen["doorbells"]:
                if doorbell["name"] == self.name:
                    self.status = doorbell["enabled"]
                    return doorbell
        except (TypeError, KeyError):
            pass
        return {}

    async def get_network_info(self) -> bool:
        """Get network info for sync-less module."""
        return True

    @property
    def network_info(self) -> dict:
        """Format lotus response to resemble sync module."""
        return {
            "network": {
                "id": self.network_id,
                "name": self.name,
                "armed": self.status,
                "sync_module_error": False,
                "account_id": self.blink.account_id,
            }
        }

    @network_info.setter
    def network_info(self, value: str):
        """Set network_info property."""


class LocalStorageMediaItem:
    """Metadata of media item in the local storage manifest."""

    def __init__(
        self,
        item_id: str,
        camera_name: str,
        created_at: str,
        size: str,
        manifest_id: str,
        url_template: str,
    ) -> None:
        """Initialize media item.

        :param item_id: ID of the manifest item.
        :param camera_name: Name of camera that took the video.
        :param created_at: ISO-formatted time stamp for creation time.
        :param size: Size of the video file.
        """
        self._id = int(item_id)
        self._camera_name = camera_name
        self._created_at = datetime.datetime.fromisoformat(created_at)
        self._size = size
        self._url_template = url_template
        self._manifest_id = manifest_id

    def _build_url(self, manifest_id: str, clip_id: str) -> str:
        return string.Template(self._url_template).substitute(
            manifest_id=manifest_id, clip_id=clip_id
        )

    @property
    def id(self) -> int:
        """Return media item ID."""
        return self._id

    @property
    def name(self) -> str:
        """Return name of camera that captured this media item."""
        return self._camera_name

    @property
    def created_at(self) -> datetime.datetime:
        """Return the ISO-formatted creation time stamp of this media item."""
        return self._created_at

    @property
    def size(self) -> str:
        """Return the reported size of this media item."""
        return self._size

    def url(self, manifest_id: str = "") -> str:
        """Build the URL new each time since the media item is cached, and the manifest is possibly rebuilt each refresh.

        :param manifest_id: ID of new manifest (if it changed)
        :return: URL for clip retrieval
        """
        if manifest_id:
            self._manifest_id = manifest_id
        return self._build_url(self._manifest_id, str(self._id))

    async def prepare_download(
        self, blink: Blink, max_retries: int = 4
    ) -> dict | None:
        """Initiate upload of media item from the sync module to Blink cloud servers."""
        url = blink.urls.base_url + self.url()
        response = None
        for retry in range(max_retries):
            response = await api.http_post(blink, url)
            if isinstance (response,dict) and "id" in response:
                break
            seconds = backoff_seconds(retry=retry, default_time=3)
            _LOGGER.debug(
                "[retry=%d] Retrying in %d seconds: %s", retry + 1, seconds, url
            )
            await asyncio.sleep(seconds)
        if isinstance (response,dict):
            return response
        return {}

    def __repr__(self) -> str:
        """Create string representation."""
        return (
            f"LocalStorageMediaItem(id={self._id}, camera_name={self._camera_name}, created_at={self._created_at}"
            + f", size={self._size}, manifest_id={self._manifest_id}, url_template={self._url_template})"
        )

    def __str__(self):
        """Create string representation."""
        return self.__repr__()

    def cmp_key(self) -> datetime.datetime:
        """Return key to use for comparison."""
        return self._created_at

    def __eq__(self, other) -> bool:
        """Check equality."""
        return self.cmp_key() == other.cmp_key()

    def __lt__(self, other) -> bool:
        """Check less than."""
        return self.cmp_key() < other.cmp_key()

    def __hash__(self) -> int:
        """Return unique hash value."""
        return self._id
