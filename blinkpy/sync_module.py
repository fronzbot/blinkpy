"""Defines a sync module for Blink."""

import logging

from requests.structures import CaseInsensitiveDict
from blinkpy import api
from blinkpy.camera import BlinkCamera
from blinkpy.helpers.constants import ONLINE

_LOGGER = logging.getLogger(__name__)


class BlinkSyncModule():
    """Class to initialize sync module."""

    def __init__(self, blink, network_name, network_id):
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
        self.homescreen = None
        self.network_info = None
        self.events = []
        self.cameras = CaseInsensitiveDict({})
        self.motion = {}
        self.last_record = {}

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
        return self.network_info['network']['armed']

    @arm.setter
    def arm(self, value):
        """Arm or disarm system."""
        if value:
            return api.request_system_arm(self.blink, self.network_id)

        return api.request_system_disarm(self.blink, self.network_id)

    def start(self):
        """Initialize the system."""
        response = api.request_syncmodule(self.blink, self.network_id)
        self.summary = response['syncmodule']
        self.sync_id = self.summary['id']
        self.network_id = self.summary['network_id']
        self.serial = self.summary['serial']
        self.status = self.summary['status']

        self.events = self.get_events()
        self.homescreen = api.request_homescreen(self.blink)
        self.network_info = api.request_network_status(self.blink,
                                                       self.network_id)

        self.check_new_videos()
        camera_info = self.get_camera_info()
        for camera_config in camera_info:
            name = camera_config['name']
            self.cameras[name] = BlinkCamera(self)
            self.motion[name] = False
            self.cameras[name].update(camera_config, force_cache=True)

    def get_events(self):
        """Retrieve events from server."""
        response = api.request_sync_events(self.blink, self.network_id)
        return response['event']

    def get_camera_info(self):
        """Retrieve camera information."""
        response = api.request_cameras(self.blink, self.network_id)
        return response['devicestatus']

    def refresh(self, force_cache=False):
        """Get all blink cameras and pulls their most recent status."""
        self.events = self.get_events()
        self.homescreen = api.request_homescreen(self.blink)
        self.network_info = api.request_network_status(self.blink,
                                                       self.network_id)
        camera_info = self.get_camera_info()
        self.check_new_videos()
        for camera_config in camera_info:
            name = camera_config['name']
            self.cameras[name].update(camera_config, force_cache=force_cache)

    def check_new_videos(self):
        """Check if new videos since last refresh."""
        resp = api.request_videos(self.blink,
                                  time=self.blink.last_refresh,
                                  page=0)
        try:
            info = resp['videos']
        except (KeyError, TypeError):
            _LOGGER.warning("Could not check for motion. Response: %s", resp)
            return False

        for camera in self.cameras.keys():
            self.motion[camera] = False

        for entry in info:
            try:
                name = entry['camera_name']
                clip = entry['address']
                timestamp = entry['created_at']
                self.motion[name] = True
                self.last_record[name] = {'clip': clip, 'time': timestamp}
            except KeyError:
                _LOGGER.info("Could not extract info from video entry.")

        return True
