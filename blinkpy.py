#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
blinkpy by Kevin Fronczak - A Blink camera Python library.

https://github.com/fronzbot/blinkpy
Original protocol hacking by MattTW :
https://github.com/MattTW/BlinkMonitorProtocol
Published under the MIT license - See LICENSE file for more details.
"Blink Wire-Free HS Home Monitoring & Alert Systems" is a trademark
owned by Immedia Inc., see www.blinkforhome.com for more information.
I am in no way affiliated with Blink, nor Immedia Inc.
"""

import json
import getpass
from shutil import copyfileobj
import requests
import helpers.errors as ERROR
from helpers.constants import (BLINK_URL, LOGIN_URL,
                               LOGIN_BACKUP_URL,
                               DEFAULT_URL, ONLINE)


def _attempt_reauthorization(blink):
    """Attempt to refresh auth token and links."""
    headers = blink.get_auth_token()
    blink.set_links()
    return headers


def _request(blink, url='http://google.com', data=None, headers=None,
             reqtype='get', stream=False, json_resp=True, is_retry=False):
    """Wrapper function for request."""
    if reqtype == 'post':
        response = requests.post(url, headers=headers,
                                 data=data)
    elif reqtype == 'get':
        response = requests.get(url, headers=headers,
                                stream=stream)
    else:
        raise BlinkException(ERROR.REQUEST)

    if json_resp and 'code' in response.json():
        if is_retry:
            raise BlinkAuthenticationException(
                (response.json()['code'], response.json()['message']))
        else:
            headers = _attempt_reauthorization(blink)
            return _request(blink, url=url, data=data, headers=headers,
                            reqtype=reqtype, stream=stream,
                            json_resp=json_resp, is_retry=True)

    if json_resp:
        return response.json()
    else:
        return response


# pylint: disable=super-init-not-called
class BlinkException(Exception):
    """Class to throw general blink exception."""

    def __init__(self, errcode):
        """Initialize BlinkException."""
        self.errid = errcode[0]
        self.message = errcode[1]


class BlinkAuthenticationException(BlinkException):
    """Class to throw authentication exception."""

    pass


class BlinkURLHandler(object):
    """Class that handles Blink URLS."""

    def __init__(self, region_id):
        """Initialize the urls."""
        self.base_url = 'https://' + region_id + '.' + BLINK_URL
        self.home_url = self.base_url + '/homescreen'
        self.event_url = self.base_url + '/events/network/'
        self.network_url = self.base_url + '/network/'
        self.networks_url = self.base_url + '/networks'


class BlinkCamera(object):
    """Class to initialize individual camera."""

    def __init__(self, config, blink):
        """Initiailize BlinkCamera."""
        self.blink = blink
        self.urls = self.blink.urls
        self.id = str(config['device_id'])  # pylint: disable=invalid-name
        self.name = config['name']
        self._status = config['armed']
        self.thumbnail = self.urls.base_url + config['thumbnail'] + '.jpg'
        self.clip = self.urls.base_url + config['thumbnail'] + '.mp4'
        self.temperature = config['temp']
        self.battery = config['battery']
        self.notifications = config['notifications']
        self.motion = {}
        self.header = None
        self.image_link = None
        self.arm_link = None
        self.region_id = config['region_id']

    @property
    def armed(self):
        """Return camera arm status."""
        return self._status

    @property
    def battery_string(self):
        """Return string indicating battery status."""
        if self.battery > 1 and self.battery <= 3:
            return "OK"
        elif self.battery >= 0:
            return "Low"
        else:
            return "Unknown"

    def snap_picture(self):
        """Take a picture with camera to create a new thumbnail."""
        _request(self.blink, url=self.image_link,
                 headers=self.header, reqtype='post')

    def set_motion_detect(self, enable):
        """Set motion detection."""
        url = self.arm_link
        if enable:
            _request(self.blink, url=url + 'enable',
                     headers=self.header, reqtype='post')
        else:
            _request(self.blink, url=url + 'disable',
                     headers=self.header, reqtype='post')

    def update(self, values):
        """Update camera information."""
        self.name = values['name']
        self._status = values['armed']
        self.thumbnail = self.urls.base_url + values['thumbnail'] + '.jpg'
        self.clip = self.urls.base_url + values['thumbnail'] + '.mp4'
        self.temperature = values['temp']
        self.battery = values['battery']
        self.notifications = values['notifications']

    def image_refresh(self):
        """Refresh current thumbnail."""
        url = self.urls.home_url
        response = _request(self.blink, url=url, headers=self.header,
                            reqtype='get')['devices']
        for element in response:
            try:
                if str(element['device_id']) == self.id:
                    self.thumbnail = (self.urls.base_url +
                                      element['thumbnail'] + '.jpg')
                    return self.thumbnail
            except KeyError:
                pass
        return None

    def image_to_file(self, path):
        """Write image to file."""
        thumb = self.image_refresh()
        response = _request(self.blink, url=thumb, headers=self.header,
                            reqtype='get', stream=True, json_resp=False)
        if response.status_code == 200:
            with open(path, 'wb') as imgfile:
                copyfileobj(response.raw, imgfile)


class Blink(object):
    """Class to initialize communication and sync module."""

    def __init__(self, username=None, password=None):
        """Initialize Blink system."""
        self._username = username
        self._password = password
        self._token = None
        self._auth_header = None
        self.network_id = None
        self.account_id = None
        self.region = None
        self.region_id = None
        self._host = None
        self._events = []
        self.cameras = {}
        self._idlookup = {}
        self.urls = None

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
    def events(self):
        """Get all events on server."""
        url = self.urls.event_url + self.network_id
        headers = self._auth_header
        self._events = _request(self, url=url, headers=headers,
                                reqtype='get')['event']
        return self._events

    @property
    def online(self):
        """Return boolean system online status."""
        url = self.urls.network_url + self.network_id + '/syncmodules'
        headers = self._auth_header
        return ONLINE[_request(self, url=url, headers=headers,
                               reqtype='get')['syncmodule']['status']]

    def last_motion(self):
        """Find last motion of each camera."""
        recent = self.events
        for element in recent:
            try:
                camera_id = str(element['camera_id'])
                camera_name = self.id_table[camera_id]
                camera = self.cameras[camera_name]
                if element['type'] == 'motion':
                    url = self.urls.base_url + element['video_url']
                    camera.motion = {'video': url,
                                     'image': url[:-3] + 'jpg',
                                     'time': element['created_at']}
            except KeyError:
                pass

    @property
    def arm(self):
        """Return status of sync module: armed/disarmed."""
        return self.get_summary()['network']['armed']

    @arm.setter
    def arm(self, value):
        """Arm or disarm system."""
        if value:
            value_to_append = 'arm'
        else:
            value_to_append = 'disarm'
        url = self.urls.network_url + self.network_id + '/' + value_to_append
        _request(self, url=url, headers=self._auth_header, reqtype='post')

    def refresh(self):
        """Get all blink cameras and pulls their most recent status."""
        response = self.get_summary()['devices']

        for name in self.cameras:
            camera = self.cameras[name]
            for element in response:
                try:
                    if str(element['device_id']) == camera.id:
                        camera.update(element)
                except KeyError:
                    pass
        return None

    def get_summary(self):
        """Get a full summary of device information."""
        url = self.urls.home_url
        headers = self._auth_header

        if self._auth_header is None:
            raise BlinkException(ERROR.AUTH_TOKEN)

        return _request(self, url=url, headers=headers, reqtype='get')

    def get_cameras(self):
        """Find and creates cameras."""
        response = self.get_summary()['devices']
        for element in response:
            if ('device_type' in element and
                    element['device_type'] == 'camera'):
                # Add region to config
                element['region_id'] = self.region_id
                device = BlinkCamera(element, self)
                self.cameras[device.name] = device
                self._idlookup[device.id] = device.name

    def set_links(self):
        """Set access links and required headers for each camera in system."""
        for name in self.cameras:
            camera = self.cameras[name]
            network_id_url = self.urls.network_url + self.network_id
            image_url = network_id_url + '/camera/' + camera.id + '/thumbnail'
            arm_url = network_id_url + '/camera/' + camera.id + '/'
            camera.image_link = image_url
            camera.arm_link = arm_url
            camera.header = self._auth_header

    def setup_system(self):
        """
        Wrapper for various setup functions.

        Method logs in and sets auth token, urls, and ids for future requests.
        """
        if self._username is None or self._password is None:
            raise BlinkAuthenticationException(ERROR.AUTHENTICATE)

        self.get_auth_token()
        self.get_ids()
        self.get_cameras()
        self.set_links()

    def login(self):
        """Prompt user for username and password."""
        self._username = input("Username:")
        self._password = getpass.getpass("Password:")

    def get_auth_token(self):
        """Retrieve the authentication token from Blink."""
        if not isinstance(self._username, str):
            raise BlinkAuthenticationException(ERROR.USERNAME)
        if not isinstance(self._password, str):
            raise BlinkAuthenticationException(ERROR.PASSWORD)

        headers = {'Host': DEFAULT_URL,
                   'Content-Type': 'application/json'}
        data = json.dumps({
            "email": self._username,
            "password": self._password,
            "client_specifier": "iPhone 9.2 | 2.2 | 222"
        })
        response = _request(self, url=LOGIN_URL, headers=headers,
                            data=data, json_resp=False, reqtype='post')
        if response.status_code is 200:
            response = response.json()
            (self.region_id, self.region), = response['region'].items()
        else:
            response = _request(self, url=LOGIN_BACKUP_URL, headers=headers,
                                data=data, reqtype='post')
            self.region_id = 'rest.piri'
            self.region = "UNKNOWN"

        self._host = self.region_id + '.' + BLINK_URL
        self._token = response['authtoken']['authtoken']

        self._auth_header = {'Host': self._host,
                             'TOKEN_AUTH': self._token}

        self.urls = BlinkURLHandler(self.region_id)

        return self._auth_header

    def get_ids(self):
        """Set the network ID and Account ID."""
        url = self.urls.networks_url
        headers = self._auth_header

        if self._auth_header is None:
            raise BlinkException(ERROR.AUTH_TOKEN)

        response = _request(self, url=url, headers=headers, reqtype='get')
        self.network_id = str(response['networks'][0]['id'])
        self.account_id = str(response['networks'][0]['account_id'])
