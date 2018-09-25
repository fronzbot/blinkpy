"""Defines a sync module for Blink."""

import logging
import time

from requests.structures import CaseInsensitiveDict
from blinkpy.camera import BlinkCamera
from blinkpy.helpers.util import http_req, BlinkException
from blinkpy.helpers.constants import ONLINE
import blinkpy.helpers.errors as ERROR

_LOGGER = logging.getLogger(__name__)


class BlinkSyncModule():
    """Class to initialize sync module."""

    def __init__(self, blink, header, urls):
        """Initialize Blink sync module."""
        self.blink = blink
        self._auth_header = header
        self.sync_id = None
        self.region = None
        self.region_id = None
        self._host = None
        self._events = []
        self.cameras = CaseInsensitiveDict({})
        self._idlookup = {}
        self.urls = urls
        self._video_count = 0
        self._all_videos = {}
        self._summary = None
        self.record_dates = dict()

    @property
    def camera_thumbs(self):
        """Return camera thumbnails."""
        self.refresh()
        data = {}
        for name, camera in self.cameras.items():
            data[name] = camera.thumbnail

        return data

    @property
    def id_table(self):
        """Return id/camera pairs."""
        return self._idlookup

    @property
    def video_count(self):
        """Return number of videos on server."""
        url = "{}/count".format(self.urls.video_url)
        headers = self._auth_header
        self._video_count = http_req(self.blink, url=url, headers=headers,
                                     reqtype='get')['count']
        return self._video_count

    @property
    def events(self):
        """Get all events on server."""
        return self._events

    @property
    def online(self):
        """Return boolean system online status."""
        return ONLINE[self._status_request()['syncmodule']['status']]

    @property
    def videos(self):
        """Return video list."""
        return self._all_videos

    @property
    def summary(self):
        """Get a full summary of device information."""
        return self._summary

    @property
    def arm(self):
        """Return status of sync module: armed/disarmed."""
        return self.summary['network']['armed']

    @arm.setter
    def arm(self, value):
        """Arm or disarm system."""
        if value:
            value_to_append = 'arm'
        else:
            value_to_append = 'disarm'
        url = "{}/{}/{}".format(self.urls.network_url,
                                self.blink.network_id,
                                value_to_append)
        http_req(self.blink, url=url, headers=self._auth_header,
                 reqtype='post')

    def refresh(self, force_cache=False):
        """Get all blink cameras and pulls their most recent status."""
        self._summary = self._summary_request()
        self._events = self.blink.events_request()
        response = self.summary['devices']
        self.get_videos()
        for name in self.cameras:
            camera = self.cameras[name]
            for element in response:
                try:
                    if str(element['device_id']) == camera.id:
                        element['video'] = self.videos[name][0]['clip']
                        thumb = self.videos[name][0]['thumb']
                        element['thumbnail'] = thumb
                        camera.update(element, force_cache=force_cache)
                except KeyError:
                    pass

    def get_videos(self, start_page=0, end_page=1):
        """Retrieve last recorded videos per camera."""
        videos = list()
        all_dates = dict()
        for page_num in range(start_page, end_page + 1):
            this_page = self._video_request(page_num)
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
                if camera_name not in all_dates:
                    all_dates[camera_name] = list()
                all_dates[camera_name].append(clip_date)
                try:
                    self._all_videos[camera_name].append(
                        {
                            'clip': clip_addr,
                            'thumb': thumb_addr,
                        }
                    )
                except KeyError:
                    self._all_videos[camera_name] = [
                        {
                            'clip': clip_addr,
                            'thumb': thumb_addr,
                        }
                    ]
        self.record_dates = all_dates

    def get_cameras(self):
        """Find and creates cameras."""
        self._summary = self._summary_request()
        response = self.summary['devices']
        for element in response:
            if ('device_type' in element and
                    element['device_type'] == 'camera'):
                # Add region to config
                element['region_id'] = self.region_id
                try:
                    name = element['name']
                    element['video'] = self.videos[name][0]['clip']
                    element['thumbnail'] = self.videos[name][0]['thumb']
                except KeyError:
                    element['video'] = None
                    element['thumbnail'] = None
                device = BlinkCamera(element, self)
                self.cameras[device.name] = device
                self._idlookup[device.id] = device.name
        self.refresh()

    def set_links(self):
        """Set access links and required headers for each camera in system."""
        for name in self.cameras:
            camera = self.cameras[name]
            network_id_url = "{}/{}".format(self.urls.network_url,
                                            self.blink.network_id)
            image_url = "{}/camera/{}/thumbnail".format(network_id_url,
                                                        camera.id)
            arm_url = "{}/camera/{}/".format(network_id_url,
                                             camera.id)
            camera.image_link = image_url
            camera.arm_link = arm_url
            camera.header = self._auth_header

    def _video_request(self, page=0):
        """Perform a request for videos."""
        url = "{}/page/{}".format(self.urls.video_url, page)
        headers = self._auth_header
        return http_req(self.blink, url=url, headers=headers, reqtype='get')

    def _status_request(self):
        """Get syncmodule status."""
        url = "{}/{}/syncmodules".format(self.urls.network_url,
                                         self.blink.network_id)
        headers = self._auth_header
        return http_req(self.blink, url=url, headers=headers, reqtype='get')

    def camera_config_request(self, camera_id):
        """Retrieve more info about Blink config."""
        url = "{}/network/{}/camera/{}/config".format(self.urls.base_url,
                                                      self.blink.network_id,
                                                      str(camera_id))
        headers = self._auth_header
        return http_req(self.blink, url=url, headers=headers, reqtype='get')
