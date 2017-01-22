#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
blinkpy by Kevin Fronczak - A Blink camera Python library
https://github.com/fronzbot/blinkpy
Original protocol hacking by MattTW : https://github.com/MattTW/BlinkMonitorProtocol

Published under the MIT license - See LICENSE file for more details.

"Blink Wire-Free HS Home Monitoring & Alert Systems" is a trademark owned by Immedia Inc., see www.blinkforhome.com for more information.
I am in no way affiliated with Blink, nor Immedia Inc.
'''

import logging
import requests
import getpass
import json

__version__ = '0.2.0'

LOGIN_URL = 'https://prod.immedia-semi.com/login'
BASE_URL  = 'https://prod.immedia-semi.com'
HOST_URL  = 'prod.immedia-semi.com'

logger = logging.getLogger('blinkpy')


def _request(url, data=None, headers=None, type='get'):
    """Wrapper function for request"""
    if type is 'post':
        response = requests.post(url, headers=headers, data=data).json()
    elif type is 'get':
        response = requests.get(url, headers=headers).json()
    else:
        raise ValueError("Cannot perform requests of type " + type)

    if 'message' in response.keys():
        raise BlinkAuthenticationException(response['code'], response['message'])

    return response


class BlinkException(Exception):
    def __init__(self, id, message):
        self.id = id
        self.message = message


class BlinkAuthenticationException(BlinkException):
    pass


class BlinkCamera(object):
    """Class to initialize individual camera"""
    def __init__(self, name, id, status, thumb, clip, temperature, battery, notifications):
        self._ID            = id
        self._NAME          = name
        self._STATUS        = status
        self._THUMB         = thumb
        self._CLIP          = clip
        self._TEMPERATURE   = temperature
        self._BATTERY       = battery
        self._NOTIFICATIONS = notifications
        self._MOTION        = {}
        self._HEADER        = None
        self._IMAGE_LINK    = None
        self._ARM_LINK      = None

    @property
    def id(self):
        return self._ID

    @property
    def name(self):
        return self._NAME

    @name.setter
    def name(self, value):
        self._NAME = value

    @property
    def armed(self):
        return self._STATUS

    @property
    def clip(self):
        return self._CLIP

    @clip.setter
    def clip(self, value):
        self._CLIP = value

    @property
    def thumbnail(self):
        return self._THUMB

    @thumbnail.setter
    def thumbnail(self, value):
        self._THUMB = value

    @property
    def temperature(self):
        return self._TEMPERATURE

    @temperature.setter
    def temperature(self, value):
        self._TEMPERATURE = value

    @property
    def battery(self):
        return self._BATTERY

    @battery.setter
    def battery(self, value):
        self._BATTERY = value

    @property
    def notifications(self):
        return self._NOTIFICATIONS

    @notifications.setter
    def notifications(self, value):
        self._NOTIFICATIONS = value

    @property
    def image_link(self):
        return self._IMAGE_LINK

    @image_link.setter
    def image_link(self, value):
        self._IMAGE_LINK = value

    @property
    def arm_link(self):
        return self._ARM_LINK

    @arm_link.setter
    def arm_link(self, value):
        self._ARM_LINK = value

    @property
    def header(self):
        return self._HEADER

    @header.setter
    def header(self, value):
        self._HEADER = value

    @property
    def motion(self):
        return self._MOTION

    @motion.setter
    def motion(self, value):
        """Sets link to last motion and timestamp"""
        self._MOTION = value

    def snap_picture(self):
        """Takes a picture with camera to create a new thumbnail"""
        _request(self._IMAGE_LINK, headers=self._HEADER, type='post')

    def set_motion_detect(self, enable):
        """Sets motion detection"""
        url = self._ARM_LINK
        if enable:
            _request(url + 'enable', headers=self._HEADER, type='post')
        else:
            _request(url + 'disable', headers=self._HEADER, type='post')

    def update(self, values):
        self._NAME          = values['name']
        self._STATUS        = values['armed']
        self._THUMB         = BASE_URL + values['thumbnail'] + '.jpg'
        self._CLIP          = BASE_URL + values['thumbnail'] + '.mp4'
        self._TEMPERATURE   = values['temp']
        self._BATTERY       = values['battery']
        self._NOTIFICATIONS = values['notifications']


class Blink(object):
    """Class to initialize communication and sync module"""
    def __init__(self, username=None, password=None):
        """Constructor for class"""
        self._username      = username
        self._password      = password
        self._TOKEN         = None
        self._AUTH_HEADER   = None
        self._NETWORKID     = None
        self._ACCOUNTID     = None
        self._EVENTS        = []
        self._CAMERAS       = []

    @property
    def cameras(self):
        return self._CAMERAS

    @property
    def network_id(self):
        return self._NETWORKID

    @property
    def account_id(self):
        return self._ACCOUNTID

    @property
    def events(self):
        """Gets all events on server"""
        url = BASE_URL + '/events/network/' + self._NETWORKID
        headers = self._AUTH_HEADER
        self._EVENTS = _request(url, headers=headers, type='get')['events']
        return self._EVENTS

    @property
    def online(self):
        """Returns True or False depending on if sync module is online/offline"""
        url = BASE_URL + 'network/' + self._NETWORKID + '/syncmodules'
        headers = self._AUTH_HEADER
        online_dict = {'online': True, 'offline': False}
        return online_dict[_request(url, headers=headers, type='get')['syncmodule']['status']]

    def last_motion(self):
        """Finds last motion of each camera"""
        recent = self.events
        for element in recent:
            try:
                camera_id = element['camera_id']
                if element['type'] == 'motion':
                    url = BASE_URL + element['video_url']
                    self._CAMERAS[str(camera_id)].motion = {'video': url, 'image': url[:-3] + 'jpg', 'time': element['created_at']}
            except KeyError:
                pass

    @property
    def arm(self):
        """Returns status of sync module: armed/disarmed"""
        return self.get_summary()['network']['armed']

    @arm.setter
    def arm(self, value):
        """Arms or disarms system.  Arms/disarms all if camera not named"""
        if value:
            value_to_append = 'arm'
        else:
            value_to_append = 'disarm'
        url = BASE_URL + '/network/' + self._NETWORKID + '/' + value_to_append
        _request(url, headers=self._AUTH_HEADER, type='post')

    def refresh(self):
        """Gets all blink cameras and pulls their most recent status"""
        response = self.get_summary()['devices']

        for camera in self._CAMERAS:
            for element in response:
                try:
                    if element['id'] == camera.id:
                        camera.update(element)
                except KeyError:
                    pass

    def get_summary(self):
        """Gets a full summary of device information"""
        url     = BASE_URL + '/homescreen'
        headers = self._AUTH_HEADER

        if self._AUTH_HEADER is None:
            raise BlinkException(0, "Authentication header incorrect.  Are you sure you logged in and received your token?")

        return _request(url, headers=headers, type='get')

    def get_cameras(self):
        """Finds and creates cameras"""
        response = self.get_summary()['devices']
        for element in response:
            if 'device_type' in element.keys():
                if element['device_type'] == 'camera':
                    self._CAMERAS.append(
                        BlinkCamera(
                            element['name'],
                            str(element['device_id']),
                            element['armed'],
                            BASE_URL + element['thumbnail'] + '.jpg',
                            BASE_URL + element['thumbnail'] + '.mp4',
                            element['temp'],
                            element['battery'],
                            element['notifications']
                        )
                    )

    def set_links(self):
        """Sets access links and required headers for each camera in system"""
        for camera in self._CAMERAS:
            image_url = BASE_URL + '/network/' + self._NETWORKID + '/camera/' + camera.id + '/thumbnail'
            arm_url   = BASE_URL + '/network/' + self._NETWORKID + '/camera/' + camera.id + '/'
            camera.image_link = image_url
            camera.arm_link = arm_url
            camera.header = self._AUTH_HEADER

    def setup_system(self):
        """Method logs in and sets auth token and network ids for future requests"""
        if self._username is None or self._password is None:
            raise BlinkAuthenticationException(3, "Cannot authenticate since either password or username has not been set")

        self.get_auth_token()
        self.get_ids()
        self.get_cameras()
        self.set_links()

    def login(self):
        """Prompts user for username and password"""
        self._username = input("Username:")
        self._password = getpass.getpass("Password:")

    def get_auth_token(self):
        """Retrieves the authentication token from Blink"""
        if not isinstance(self._username, str):
            raise BlinkAuthenticationException(0, "Username must be a string")
        if not isinstance(self._password, str):
            raise BlinkAuthenticationException(0, "Password must be a string")

        headers = {'Host': HOST_URL,
                   'Content-Type': 'application/json'
                   }
        data    = json.dumps({"email": self._username,
                              "password": self._password,
                              "client_specifier": "iPhone 9.2 | 2.2 | 222"
                              })
        response = _request(LOGIN_URL, headers=headers, data=data, type='post')
        self._TOKEN = response['authtoken']['authtoken']
        self._AUTH_HEADER = {'Host': HOST_URL,
                             'TOKEN_AUTH': self._TOKEN
                             }

    def get_ids(self):
        """Sets the network ID and Account ID"""
        url     = BASE_URL + '/networks'
        headers = self._AUTH_HEADER

        if self._AUTH_HEADER is None:
            raise BlinkException(0, "Authentication header incorrect.  Are you sure you logged in and received your token?")

        response = _request(url, headers=headers, type='get')
        self._NETWORKID = str(response['networks'][0]['id'])
        self._ACCOUNTID = str(response['networks'][0]['account_id'])
