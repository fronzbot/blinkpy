"""Defines a sync module for Blink."""

import logging

from requests.structures import CaseInsensitiveDict
from blinkpy.camera import BlinkCamera
from blinkpy.helpers.util import http_req
from blinkpy.helpers.constants import ONLINE

_LOGGER = logging.getLogger(__name__)


class BlinkSyncModule():
    """Class to initialize sync module."""

    def __init__(self, blink, header, urls=None):
        """
        Initialize Blink sync module.

        :param blink: Blink class instantiation
        :param header: Blink authentication header
        :param urls: URL Handler instantiation (deprecated)
        """
        self.blink = blink
        self._auth_header = header
        self.sync_id = None
        self.region = None
        self.region_id = None
        self._host = None
        self._events = []
        self.cameras = CaseInsensitiveDict({})
        self._idlookup = {}
        self._video_count = 0
        self._all_videos = {}
        self._summary = None
        self.record_dates = dict()
        self.first_init = True

    @property
    def urls(self):
        """Return device urls."""
        return self.blink.urls

    @property
    def network_id(self):
        """Return the network id."""
        return self.blink.network_id

    @property
    def camera_thumbs(self):
        """Return camera thumbnails."""
        self.blink.refresh()
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
        self._video_count = self.http_get(url)['count']
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
        return self._summary['network']['armed']

    @arm.setter
    def arm(self, value):
        """Arm or disarm system."""
        if value:
            value_to_append = 'arm'
        else:
            value_to_append = 'disarm'
        url = "{}/{}/{}".format(self.urls.network_url,
                                self.network_id,
                                value_to_append)
        self.http_post(url)

    def refresh(self, force_cache=False):
        """Get all blink cameras and pulls their most recent status."""
        summary = self._summary_request()
        events = self._events_request()
        response = summary['devices']
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
        self._summary = summary
        self._events = events

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
        response = self._summary['devices']
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
        self.blink.refresh(force_cache=self.first_init)
        self.first_init = False

    def set_links(self):
        """Set access links and required headers for each camera in system."""
        for name in self.cameras:
            camera = self.cameras[name]
            network_id_url = "{}/{}".format(self.urls.network_url,
                                            self.network_id)
            image_url = "{}/camera/{}/thumbnail".format(network_id_url,
                                                        camera.id)
            arm_url = "{}/camera/{}/".format(network_id_url,
                                             camera.id)
            camera.image_link = image_url
            camera.arm_link = arm_url
            camera.header = self._auth_header

    def _summary_request(self):
        """Request a summary from blink."""
        return self.blink.summary_request()

    def _events_request(self):
        """Request a list of events from blink."""
        return self.blink.events_request()

    def _video_request(self, page=0):
        """Perform a request for videos."""
        url = "{}/page/{}".format(self.urls.video_url, page)
        return self.http_get(url)

    def _status_request(self):
        """Get syncmodule status."""
        url = "{}/{}/syncmodules".format(self.urls.network_url,
                                         self.network_id)
        return self.http_get(url)

    def camera_config_request(self, camera_id):
        """Retrieve more info about Blink config."""
        url = "{}/network/{}/camera/{}/config".format(self.urls.base_url,
                                                      self.network_id,
                                                      str(camera_id))
        return self.http_get(url)

    def http_get(self, url, stream=False, json=True):
        """
        Perform an http get request.

        :param url: URL to perform get request
        :param stream: Stream response? True/FALSE
        :param json: Return json response? TRUE/False
        """
        return http_req(self.blink, url=url, headers=self._auth_header,
                        reqtype='get', stream=stream, json_resp=json)

    def http_post(self, url):
        """Perform a post request.

        :param url: URL to perform post request
        """
        return http_req(self.blink, url=url, headers=self._auth_header,
                        reqtype='post')
