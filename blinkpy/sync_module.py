"""Defines a sync module for Blink."""

import logging

from requests.structures import CaseInsensitiveDict
from blinkpy import api
from blinkpy.camera import BlinkCamera
from blinkpy.helpers.constants import ONLINE

_LOGGER = logging.getLogger(__name__)


class BlinkSyncModule():
    """Class to initialize sync module."""

    def __init__(self, blink):
        """
        Initialize Blink sync module.

        :param blink: Blink class instantiation
        """
        self.blink = blink
        self._auth_header = blink.auth_header
        self.network_id = blink.network_id
        self.region = blink.region
        self.region_id = blink.region_id
        self.name = 'sync'
        self.serial = None
        self.status = None
        self.sync_id = None
        self.host = None
        self.summary = None
        self.homescreen = None
        self.record_dates = {}
        self.videos = {}
        self.events = []
        self.cameras = CaseInsensitiveDict({})
        self.all_clips = {}

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
        return self.homescreen['network']['armed']

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
        self.name = self.summary['name']
        self.sync_id = self.summary['id']
        self.network_id = self.summary['network_id']
        self.serial = self.summary['serial']
        self.status = self.summary['status']

        self.events = self.get_events()

        self.homescreen = api.request_homescreen(self.blink)

        camera_info = self.get_camera_info()
        for camera_config in camera_info:
            name = camera_config['name']
            self.cameras[name] = BlinkCamera(self)

        self.videos = self.get_videos()
        for camera_config in camera_info:
            name = camera_config['name']
            if name in self.cameras:
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
        self.videos = self.get_videos()
        self.homescreen = api.request_homescreen(self.blink)
        camera_info = self.get_camera_info()
        for camera_config in camera_info:
            name = camera_config['name']
            self.cameras[name].update(camera_config, force_cache=force_cache)

    def get_videos(self, start_page=0, end_page=1):
        """
        Retrieve last recorded videos per camera.

        :param start_page: Page to start reading from on blink servers
                           (defaults to 0)
        :param end_page: Page to stop reading from (defaults to 1)
        """
        videos = list()
        all_dates = dict()

        for page_num in range(start_page, end_page + 1):
            this_page = api.request_videos(self.blink, page=page_num)
            if not this_page:
                break
            videos.append(this_page)

        for page in videos:
            _LOGGER.debug("Retrieved video page %s", page)
            for entry in page:
                camera_name = entry['camera_name']
                clip_addr = entry['address']
                thumb_addr = entry['thumbnail']
                clip_date = clip_addr.split('_')[-6:]
                clip_date = '_'.join(clip_date)
                clip_date = clip_date.split('.')[0]
                try:
                    self.all_clips[camera_name][clip_date] = clip_addr
                except KeyError:
                    self.all_clips[camera_name] = {clip_date: clip_addr}

                if camera_name not in all_dates:
                    all_dates[camera_name] = list()
                all_dates[camera_name].append(clip_date)
                try:
                    self.videos[camera_name].append(
                        {
                            'clip': clip_addr,
                            'thumb': thumb_addr,
                        }
                    )
                except KeyError:
                    self.videos[camera_name] = [
                        {
                            'clip': clip_addr,
                            'thumb': thumb_addr,
                        }
                    ]
        self.record_dates = all_dates

        return self.videos
