#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
blinkpy by Kevin Fronczak - A Blink camera Python library
https://github.com/fronzbot/blinkpy
Original protocol hacking by MattTW :
https://github.com/MattTW/BlinkMonitorProtocol
Published under the MIT license - See LICENSE file for more details.
"Blink Wire-Free HS Home Monitoring & Alert Systems" is a trademark
owned by Immedia Inc., see www.blinkforhome.com for more information.
I am in no way affiliated with Blink, nor Immedia Inc.
'''

import json
import getpass
import requests
import errors as ERROR
from constants import (BLINK_URL, LOGIN_URL,
                       DEFAULT_URL, ONLINE)


def _request(url, data=None, headers=None, reqtype='get',
             stream=False, json_resp=True):
    """Wrapper function for request"""
    if reqtype is 'post':
        response = requests.post(url, headers=headers,
                                 data=data).json()
    elif reqtype is 'get' and json_resp:
        response = requests.get(url, headers=headers,
                                stream=stream).json()
    elif reqtype is 'get' and not json_resp:
        response = requests.get(url, headers=headers,
                                stream=stream)
    else:
        raise BlinkException(ERROR.REQUEST)

    if json_resp and 'code' in response:
        raise BlinkAuthenticationException(
            (response['code'], response['message']))

    return response


# pylint: disable=super-init-not-called
class BlinkException(Exception):
    """
    Class to throw general blink exception.
    """
    def __init__(self, errcode):
        self.errid = errcode[0]
        self.message = errcode[1]


class BlinkAuthenticationException(BlinkException):
    """
    Class to throw authentication exception.
    """
    pass


class BlinkURLHandler(object):
    """Class that handles Blink URLS"""
    def __init__(self, region_id):
        """Initialize the urls."""
        self.base_url = 'https://' + region_id + '.' + BLINK_URL
        self.home_url = self.base_url + '/homescreen'
        self.event_url = self.base_url + '/events/network/'
        self.network_url = self.base_url + '/network/'
        self.networks_url = self.base_url + '/networks'


class BlinkCamera(object):
    """Class to initialize individual camera."""
    def __init__(self, config, urls):
        self.urls = urls
        self._id = str(config['device_id'])
        self._name = config['name']
        self._status = config['armed']
        self._thumb = self.urls.base_url + config['thumbnail'] + '.jpg'
        self._clip = self.urls.base_url + config['thumbnail'] + '.mp4'
        self._temperature = config['temp']
        self._battery = config['battery']
        self._notifications = config['notifications']
        self._motion = {}
        self._header = None
        self._image_link = None
        self._arm_link = None
        self._region_id = config['region_id']

    @property
    # pylint: disable=invalid-name
    def id(self):
        """Returns camera id"""
        return self._id

    @property
    def name(self):
        """Returns camera name"""
        return self._name

    @name.setter
    def name(self, value):
        """Sets camera name"""
        self._name = value

    @property
    def region_id(self):
        """Returns region id"""
        return self._region_id

    @property
    def armed(self):
        """Returns camera arm status"""
        return self._status

    @property
    def clip(self):
        """Returns current clip"""
        return self._clip

    @clip.setter
    def clip(self, value):
        """Sets current clip"""
        self._clip = value

    @property
    def thumbnail(self):
        """Returns current thumbnail"""
        return self._thumb

    @thumbnail.setter
    def thumbnail(self, value):
        """Sets current thumbnail"""
        self._thumb = value

    @property
    def temperature(self):
        """Returns camera temperature"""
        return self._temperature

    @temperature.setter
    def temperature(self, value):
        """Sets camera temperature"""
        self._temperature = value

    @property
    def battery(self):
        """Returns battery level"""
        return self._battery

    @battery.setter
    def battery(self, value):
        """Sets battery level"""
        self._battery = value

    @property
    def notifications(self):
        """Returns number of notifications"""
        return self._notifications

    @notifications.setter
    def notifications(self, value):
        """Sets number of notifications"""
        self._notifications = value

    @property
    def image_link(self):
        """Returns image link"""
        return self._image_link

    @image_link.setter
    def image_link(self, value):
        """Sets image link"""
        self._image_link = value

    @property
    def arm_link(self):
        """Returns link to arm camera"""
        return self._arm_link

    @arm_link.setter
    def arm_link(self, value):
        """Sets link to arm camera"""
        self._arm_link = value

    @property
    def header(self):
        """Returns request header"""
        return self._header

    @header.setter
    def header(self, value):
        """Sets request header"""
        self._header = value

    @property
    def motion(self):
        """Returns last motion event detail"""
        return self._motion

    @motion.setter
    def motion(self, value):
        """Sets link to last motion and timestamp"""
        self._motion = value

    def snap_picture(self):
        """Takes a picture with camera to create a new thumbnail"""
        _request(self._image_link, headers=self._header, reqtype='post')

    def set_motion_detect(self, enable):
        """Sets motion detection"""
        url = self._arm_link
        if enable:
            _request(url + 'enable', headers=self._header, reqtype='post')
        else:
            _request(url + 'disable', headers=self._header, reqtype='post')

    def update(self, values):
        """Updates camera information"""
        self._name = values['name']
        self._status = values['armed']
        self._thumb = self.urls.base_url + values['thumbnail'] + '.jpg'
        self._clip = self.urls.base_url + values['thumbnail'] + '.mp4'
        self._temperature = values['temp']
        self._battery = values['battery']
        self._notifications = values['notifications']

    def image_refresh(self):
        """Refreshs current thumbnail"""
        url = self.urls.home_url
        response = _request(url, headers=self._header,
                            reqtype='get')['devices']
        for element in response:
            try:
                if str(element['device_id']) == self._id:
                    self._thumb = (self.urls.base_url +
                                   element['thumbnail'] + '.jpg')
                    return self._thumb
            except KeyError:
                pass
        return None

    def image_to_file(self, path):
        """Writes image to file"""
        thumb = self.image_refresh()
        response = _request(thumb, headers=self._header,
                            stream=True, json_resp=False)
        if response.status_code == 200:
            with open(path, 'wb') as imgfile:
                for chunk in response:
                    imgfile.write(chunk)


class Blink(object):
    """Class to initialize communication and sync module"""
    def __init__(self, username=None, password=None):
        """Constructor for class"""
        self._username = username
        self._password = password
        self._token = None
        self._auth_header = None
        self._network_id = None
        self._account_id = None
        self._region = None
        self._region_id = None
        self._host = None
        self._events = []
        self._cameras = {}
        self._idlookup = {}
        self.urls = None

    @property
    def cameras(self):
        """Returns camera/id pairs"""
        return self._cameras

    @property
    def camera_thumbs(self):
        """Returns camera thumbnails"""
        self.refresh()
        data = {}
        for name, camera in self._cameras.items():
            data[name] = camera.thumbnail

        return data

    @property
    def id_table(self):
        """Returns id/camera pairs"""
        return self._idlookup

    @property
    def network_id(self):
        """Returns network id"""
        return self._network_id

    @property
    def account_id(self):
        """Returns account id"""
        return self._account_id

    @property
    def region(self):
        """Returns current region"""
        return self._region

    @property
    def region_id(self):
        """Returns region id"""
        return self._region_id

    @property
    def events(self):
        """Gets all events on server"""
        url = self.urls.event_url + self._network_id
        headers = self._auth_header
        self._events = _request(url, headers=headers,
                                reqtype='get')['event']
        return self._events

    @property
    def online(self):
        """
        Returns True or False depending on if
        sync module is online/offline
        """
        url = self.urls.network_url + self._network_id + '/syncmodules'
        headers = self._auth_header
        return ONLINE[_request(url, headers=headers,
                               reqtype='get')['syncmodule']['status']]

    def last_motion(self):
        """Finds last motion of each camera"""
        recent = self.events
        for element in recent:
            try:
                camera_id = str(element['camera_id'])
                camera_name = self._idlookup[camera_id]
                camera = self._cameras[camera_name]
                if element['type'] == 'motion':
                    url = self.urls.base_url + element['video_url']
                    camera.motion = {'video': url,
                                     'image': url[:-3] + 'jpg',
                                     'time': element['created_at']}
            except KeyError:
                pass

    @property
    def arm(self):
        """Returns status of sync module: armed/disarmed"""
        return self.get_summary()['network']['armed']

    @arm.setter
    def arm(self, value):
        """
        Arms or disarms system.
        Arms/disarms all if camera not named.
        """
        if value:
            value_to_append = 'arm'
        else:
            value_to_append = 'disarm'
        url = self.urls.network_url + self._network_id + '/' + value_to_append
        _request(url, headers=self._auth_header, reqtype='post')

    def refresh(self):
        """Gets all blink cameras and pulls their most recent status"""
        response = self.get_summary()['devices']

        for name in self._cameras:
            camera = self._cameras[name]
            for element in response:
                try:
                    if str(element['device_id']) == camera.id:
                        camera.update(element)
                except KeyError:
                    pass

    def get_summary(self):
        """Gets a full summary of device information"""
        url = self.urls.home_url
        headers = self._auth_header

        if self._auth_header is None:
            raise BlinkException(ERROR.AUTH_TOKEN)

        return _request(url, headers=headers, reqtype='get')

    def get_cameras(self):
        """Finds and creates cameras"""
        response = self.get_summary()['devices']
        for element in response:
            if ('device_type' in element and
                    element['device_type'] == 'camera'):
                # Add region to config
                element['region_id'] = self._region_id
                device = BlinkCamera(element, self.urls)
                self._cameras[device.name] = device
                self._idlookup[device.id] = device.name

    def set_links(self):
        """
        Sets access links and required headers
        for each camera in system
        """
        for name in self._cameras:
            camera = self._cameras[name]
            network_id_url = self.urls.network_url + self._network_id
            image_url = network_id_url + '/camera/' + camera.id + '/thumbnail'
            arm_url = network_id_url + '/camera/' + camera.id + '/'
            camera.image_link = image_url
            camera.arm_link = arm_url
            camera.header = self._auth_header

    def setup_system(self):
        """
        Method logs in and sets auth token and
        network ids for future requests.
        """
        if self._username is None or self._password is None:
            raise BlinkAuthenticationException(ERROR.AUTHENTICATE)

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
        response = _request(LOGIN_URL, headers=headers,
                            data=data, reqtype='post')
        self._token = response['authtoken']['authtoken']
        (self._region_id, self._region), = response['region'].items()
        self._host = self._region_id + '.' + BLINK_URL
        self._auth_header = {'Host': self._host,
                             'TOKEN_AUTH': self._token}

        self.urls = BlinkURLHandler(self._region_id)

    def get_ids(self):
        """Sets the network ID and Account ID"""
        url = self.urls.networks_url
        headers = self._auth_header

        if self._auth_header is None:
            raise BlinkException(ERROR.AUTH_TOKEN)

        response = _request(url, headers=headers, reqtype='get')
        self._network_id = str(response['networks'][0]['id'])
        self._account_id = str(response['networks'][0]['account_id'])
