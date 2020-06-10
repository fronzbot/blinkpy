"""Defines a sync module for Blink."""

import logging

from requests.structures import CaseInsensitiveDict
from blinkpy import api
from blinkpy.camera import BlinkCamera, BlinkCameraMini
from blinkpy.helpers.util import time_to_seconds
from blinkpy.helpers.constants import ONLINE

_LOGGER = logging.getLogger(__name__)


class BlinkSyncModule:
    """Class to initialize sync module."""

    def __init__(self, blink, network_name, network_id, camera_list):
        """
        Initialize Blink sync module.

        :param blink: Blink class instantiation
        """
        self.blink = blink
        self.network_id = network_id
        self.region_id = blink.auth.region_id
        self.name = network_name
        self.serial = None
        self.status = "offline"
        self.sync_id = None
        self.host = None
        self.summary = None
        self.network_info = None
        self.events = []
        self.cameras = CaseInsensitiveDict({})
        self.motion_interval = blink.motion_interval
        self.motion = {}
        self.last_record = {}
        self.camera_list = camera_list
        self.available = False

    @property
    def attributes(self):
        """Return sync attributes."""
        attr = {
            "name": self.name,
            "id": self.sync_id,
            "network_id": self.network_id,
            "serial": self.serial,
            "status": self.status,
            "region_id": self.region_id,
        }
        return attr

    @property
    def urls(self):
        """Return device urls."""
        return self.blink.urls

    @property
    def online(self):
        """Return boolean system online status."""
        try:
            return ONLINE[self.status]
        except KeyError:
            _LOGGER.error("Unknown sync module status %s", self.status)
            self.available = False
            return False

    @property
    def arm(self):
        """Return status of sync module: armed/disarmed."""
        try:
            return self.network_info["network"]["armed"]
        except (KeyError, TypeError):
            self.available = False
            return None

    @arm.setter
    def arm(self, value):
        """Arm or disarm camera."""
        if value:
            return api.request_system_arm(self.blink, self.network_id)
        return api.request_system_disarm(self.blink, self.network_id)

    def start(self):
        """Initialize the system."""
        response = self.sync_initialize()
        if not response:
            return False

        try:
            self.sync_id = self.summary["id"]
            self.serial = self.summary["serial"]
            self.status = self.summary["status"]
        except KeyError:
            _LOGGER.error(
                "Could not extract some sync module info: %s", response, exc_info=True
            )

        is_ok = self.get_network_info()
        self.check_new_videos()

        if not is_ok or not self.update_cameras():
            return False
        self.available = True
        return True

    def sync_initialize(self):
        """Initialize a sync module."""
        response = api.request_syncmodule(self.blink, self.network_id)
        try:
            self.summary = response["syncmodule"]
            self.network_id = self.summary["network_id"]
        except (TypeError, KeyError):
            _LOGGER.error(
                "Could not retrieve sync module information with response: %s", response
            )
            return False
        return response

    def update_cameras(self, camera_type=BlinkCamera):
        """Update cameras from server."""
        try:
            for camera_config in self.camera_list:
                if "name" not in camera_config:
                    break
                name = camera_config["name"]
                self.cameras[name] = camera_type(self)
                self.motion[name] = False
                camera_info = self.get_camera_info(camera_config["id"])
                self.cameras[name].update(camera_info, force_cache=True, force=True)
        except KeyError:
            _LOGGER.error("Could not create camera instances for %s", self.name)
            return False
        return True

    def get_events(self, **kwargs):
        """Retrieve events from server."""
        force = kwargs.pop("force", False)
        response = api.request_sync_events(self.blink, self.network_id, force=force)
        try:
            return response["event"]
        except (TypeError, KeyError):
            _LOGGER.error("Could not extract events: %s", response, exc_info=True)
            return False

    def get_camera_info(self, camera_id):
        """Retrieve camera information."""
        response = api.request_camera_info(self.blink, self.network_id, camera_id)
        try:
            return response["camera"][0]
        except (TypeError, KeyError):
            _LOGGER.error("Could not extract camera info: %s", response, exc_info=True)
            return []

    def get_network_info(self):
        """Retrieve network status."""
        self.network_info = api.request_network_update(self.blink, self.network_id)
        try:
            if self.network_info["network"]["sync_module_error"]:
                raise KeyError
        except (TypeError, KeyError):
            self.available = False
            return False
        return True

    def refresh(self, force_cache=False):
        """Get all blink cameras and pulls their most recent status."""
        if not self.get_network_info():
            return
        self.check_new_videos()
        for camera_name in self.cameras.keys():
            camera_id = self.cameras[camera_name].camera_id
            camera_info = self.get_camera_info(camera_id)
            self.cameras[camera_name].update(camera_info, force_cache=force_cache)
        self.available = True

    def check_new_videos(self):
        """Check if new videos since last refresh."""
        try:
            interval = self.blink.last_refresh - self.motion_interval * 60
        except TypeError:
            # This is the first start, so refresh hasn't happened yet.
            # No need to check for motion.
            return False

        resp = api.request_videos(self.blink, time=interval, page=1)

        for camera in self.cameras.keys():
            self.motion[camera] = False

        try:
            info = resp["media"]
        except (KeyError, TypeError):
            _LOGGER.warning("Could not check for motion. Response: %s", resp)
            return False

        for entry in info:
            try:
                name = entry["device_name"]
                clip = entry["media"]
                timestamp = entry["created_at"]
                if self.check_new_video_time(timestamp):
                    self.motion[name] = True and self.arm
                    self.last_record[name] = {"clip": clip, "time": timestamp}
            except KeyError:
                _LOGGER.debug("No new videos since last refresh.")

        return True

    def check_new_video_time(self, timestamp):
        """Check if video has timestamp since last refresh."""
        return time_to_seconds(timestamp) > self.blink.last_refresh


class BlinkOwl(BlinkSyncModule):
    """Representation of a sync-less device."""

    def __init__(self, blink, name, network_id, response):
        """Initialize a sync-less object."""
        cameras = [{"name": name, "id": response["id"]}]
        super().__init__(blink, name, network_id, cameras)
        self.sync_id = response["id"]
        self.serial = response["serial"]
        self.status = response["enabled"]
        if not self.serial:
            self.serial = f"{network_id}-{self.sync_id}"

    def sync_initialize(self):
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

    def update_cameras(self, camera_type=BlinkCameraMini):
        """Update sync-less cameras."""
        return super().update_cameras(camera_type=BlinkCameraMini)

    def get_camera_info(self, camera_id):
        """Retrieve camera information."""
        try:
            for owl in self.blink.homescreen["owls"]:
                if owl["name"] == self.name:
                    self.status = owl["enabled"]
                    return owl
        except KeyError:
            pass
        return None

    def get_network_info(self):
        """Get network info for sync-less module."""
        return True

    @property
    def network_info(self):
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
    def network_info(self, value):
        """Set network_info property."""
