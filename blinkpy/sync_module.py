"""Defines a sync module for Blink."""

import logging

from requests.structures import CaseInsensitiveDict
from blinkpy import api
from blinkpy.camera import BlinkCamera
from blinkpy.helpers.constants import ONLINE

_LOGGER = logging.getLogger(__name__)


class BlinkSyncModule():
    """Class to initialize sync module."""

    def __init__(self, blink, network_name, network_id, camera_list):
        """
        Initialize Blink sync module.

        :param blink: Blink class instantiation
        """
        self.blink = blink
        self._auth_header = blink.auth_header
        self.network_id = network_id
        self.region = blink.region
        self.region_id = blink.region_id
        self.name = network_name
        self.serial = None
        self.status = None
        self.sync_id = None
        self.host = None
        self.summary = None
        self.network_info = None
        self.events = []
        self.cameras = CaseInsensitiveDict({})
        self.motion = {}
        self.last_record = {}
        self.camera_list = camera_list

    @property
    def attributes(self):
        """Return sync attributes."""
        attr = {
            'name': self.name,
            'id': self.sync_id,
            'network_id': self.network_id,
            'serial': self.serial,
            'status': self.status,
            'region': self.region,
            'region_id': self.region_id,
        }
        return attr

    @property
    def urls(self):
        """Return device urls."""
        return self.blink.urls

    @property
    def online(self):
        """Return boolean system online status."""
        return ONLINE[self.status]

    @property
    def arm(self):
        """Return status of sync module: armed/disarmed."""
        try:
            return self.network_info['network']['armed']
        except (KeyError, TypeError):
            return None

    @arm.setter
    def arm(self, value):
        """Arm or disarm system."""
        if value:
            return api.request_system_arm(self.blink, self.network_id)

        return api.request_system_disarm(self.blink, self.network_id)

    def start(self):
        """Initialize the system."""
        response = api.request_syncmodule(self.blink,
                                          self.network_id)
        try:
            self.summary = response['syncmodule']
            self.network_id = self.summary['network_id']
        except (TypeError, KeyError):
            _LOGGER.error(("Could not retrieve sync module information "
                           "with response: %s"), response, exc_info=True)
            return False

        try:
            self.sync_id = self.summary['id']
            self.serial = self.summary['serial']
            self.status = self.summary['status']
        except KeyError:
            _LOGGER.error("Could not extract some sync module info: %s",
                          response,
                          exc_info=True)

        self.network_info = api.request_network_status(self.blink,
                                                       self.network_id)

        self.check_new_videos()
        try:
            for camera_config in self.camera_list:
                if 'name' not in camera_config:
                    break
                name = camera_config['name']
                self.cameras[name] = BlinkCamera(self)
                self.motion[name] = False
                camera_info = self.get_camera_info(camera_config['id'])
                self.cameras[name].update(camera_info,
                                          force_cache=True,
                                          force=True)
        except KeyError:
            _LOGGER.error("Could not create cameras instances for %s",
                          self.name,
                          exc_info=True)
            return False

        return True

    def get_events(self, **kwargs):
        """Retrieve events from server."""
        force = kwargs.pop('force', False)
        response = api.request_sync_events(self.blink,
                                           self.network_id,
                                           force=force)
        try:
            return response['event']
        except (TypeError, KeyError):
            _LOGGER.error("Could not extract events: %s",
                          response,
                          exc_info=True)
            return False

    def get_camera_info(self, camera_id):
        """Retrieve camera information."""
        response = api.request_camera_info(self.blink,
                                           self.network_id,
                                           camera_id)
        try:
            return response['camera'][0]
        except (TypeError, KeyError):
            _LOGGER.error("Could not extract camera info: %s",
                          response,
                          exc_info=True)
            return []

    def refresh(self, force_cache=False):
        """Get all blink cameras and pulls their most recent status."""
        self.network_info = api.request_network_status(self.blink,
                                                       self.network_id)
        self.check_new_videos()
        for camera_name in self.cameras.keys():
            camera_id = self.cameras[camera_name].camera_id
            camera_info = self.get_camera_info(camera_id)
            self.cameras[camera_name].update(camera_info,
                                             force_cache=force_cache)

    def check_new_videos(self):
        """Check if new videos since last refresh."""
        resp = api.request_videos(self.blink,
                                  time=self.blink.last_refresh,
                                  page=1)

        for camera in self.cameras.keys():
            self.motion[camera] = False

        try:
            info = resp['media']
        except (KeyError, TypeError):
            _LOGGER.warning("Could not check for motion. Response: %s", resp)
            return False

        for entry in info:
            try:
                name = entry['device_name']
                clip = entry['media']
                timestamp = entry['created_at']
                self.motion[name] = True
                self.last_record[name] = {'clip': clip, 'time': timestamp}
            except KeyError:
                _LOGGER.debug("No new videos since last refresh.")

        return True
