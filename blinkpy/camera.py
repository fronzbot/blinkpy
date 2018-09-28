"""Defines Blink cameras."""

from shutil import copyfileobj
import logging
from requests.exceptions import RequestException

_LOGGER = logging.getLogger(__name__)

MAX_CLIPS = 5


class BlinkCamera():
    """Class to initialize individual camera."""

    def __init__(self, config, sync):
        """Initiailize BlinkCamera."""
        self.sync = sync
        self.urls = self.sync.urls
        self.id = str(config['device_id'])  # pylint: disable=invalid-name
        self.name = config['name']
        self._status = config['active']
        self.thumbnail = "{}{}.jpg".format(self.urls.base_url,
                                           config['thumbnail'])
        self.clip = "{}{}".format(self.urls.base_url, config['video'])
        self.temperature = config['temp']
        self._battery_string = config['battery']
        self.notifications = config['notifications']
        self.motion = dict()
        self.header = None
        self.image_link = None
        self.arm_link = None
        self.region_id = config['region_id']
        self.battery_voltage = -180
        self.motion_detected = None
        self.wifi_strength = None
        self.camera_config = dict()
        self.motion_enabled = None
        self.last_record = list()
        self._cached_image = None
        self._cached_video = None

    @property
    def attributes(self):
        """Return dictionary of all camera attributes."""
        attributes = {
            'name': self.name,
            'device_id': self.id,
            'status': self._status,
            'armed': self.armed,
            'temperature': self.temperature,
            'temperature_c': self.temperature_c,
            'battery': self.battery,
            'thumbnail': self.thumbnail,
            'video': self.clip,
            'motion_enabled': self.motion_enabled,
            'notifications': self.notifications,
            'motion_detected': self.motion_detected,
            'wifi_strength': self.wifi_strength,
            'network_id': self.sync.network_id,
            'last_record': self.last_record
        }
        return attributes

    @property
    def status(self):
        """Return camera status."""
        return self._status

    @property
    def armed(self):
        """Return camera arm status."""
        return True if self._status == 'armed' else False

    @property
    def battery(self):
        """Return battery level as percentage."""
        return round(self.battery_voltage / 180 * 100)

    @property
    def battery_string(self):
        """Return string indicating battery status."""
        status = "Unknown"
        if self._battery_string > 1 and self._battery_string <= 3:
            status = "OK"
        elif self._battery_string >= 0:
            status = "Low"
        return status

    @property
    def temperature_c(self):
        """Return temperature in celcius."""
        return round((self.temperature - 32) / 9.0 * 5.0, 1)

    @property
    def image_from_cache(self):
        """Return the most recently cached image."""
        if self._cached_image:
            return self._cached_image
        return None

    @property
    def video_from_cache(self):
        """Return the most recently cached video."""
        if self._cached_video:
            return self._cached_video
        return None

    def snap_picture(self):
        """Take a picture with camera to create a new thumbnail."""
        self.sync.http_post(self.image_link)

    def set_motion_detect(self, enable):
        """Set motion detection."""
        url = self.arm_link
        if enable:
            self.sync.http_post("{}{}".format(url, 'enable'))
        else:
            self.sync.http_post("{}{}".format(url, 'disable'))

    def update(self, values, force_cache=False, skip_cache=False):
        """Update camera information."""
        self.name = values['name']
        self._status = values['active']
        self.clip = "{}{}".format(
            self.urls.base_url, values['video'])
        new_thumbnail = "{}{}.jpg".format(
            self.urls.base_url, values['thumbnail'])
        self._battery_string = values['battery']
        self.notifications = values['notifications']

        update_cached_image = False
        if new_thumbnail != self.thumbnail or self._cached_image is None:
            update_cached_image = True
        self.thumbnail = new_thumbnail
        try:
            cfg = self.sync.camera_config_request(self.id)
            self.camera_config = cfg
        except RequestException as err:
            _LOGGER.warning("Could not get config for %s with id %s",
                            self.name, self.id)
            _LOGGER.warning("Exception raised: %s", err)

        try:
            self.battery_voltage = cfg['camera'][0]['battery_voltage']
            self.motion_enabled = cfg['camera'][0]['motion_alert']
            self.wifi_strength = cfg['camera'][0]['wifi_strength']
            self.temperature = cfg['camera'][0]['temperature']
        except KeyError:
            _LOGGER.warning("Problem extracting config for camera %s",
                            self.name)

        # Check if the most recent clip is included in the last_record list
        # and that the last_record list is populated
        try:
            records = sorted(self.sync.record_dates[self.name])
            new_clip = records.pop()
            if new_clip not in self.last_record and self.last_record:
                self.motion_detected = True
                self.last_record.insert(0, new_clip)
                if len(self.last_record) > MAX_CLIPS:
                    self.last_record.pop()
            elif not self.last_record:
                self.last_record.insert(0, new_clip)
                self.motion_detected = False
            else:
                self.motion_detected = False
        except KeyError:
            _LOGGER.warning("Could not extract clip info from camera %s",
                            self.name)

        if not skip_cache:
            if update_cached_image or force_cache:
                self._cached_image = self.sync.http_get(
                    self.image_refresh(), stream=True, json=False)
            if (self.clip is None) or self.motion_detected or force_cache:
                self._cached_video = self.sync.http_get(
                    self.clip, stream=True, json=False)

    def image_refresh(self):
        """Refresh current thumbnail."""
        url = self.urls.home_url
        response = self.sync.http_get(url)['devices']
        for element in response:
            try:
                if str(element['device_id']) == self.id:
                    self.thumbnail = (
                        "{}{}.jpg".format(
                            self.urls.base_url, element['thumbnail'])
                    )
                    return self.thumbnail
            except KeyError:
                pass
        return None

    def image_to_file(self, path):
        """
        Write image to file.

        :param path: Path to write file
        """
        _LOGGER.debug("Writing image from %s to %s", self.name, path)
        response = self._cached_image
        if response.status_code == 200:
            with open(path, 'wb') as imgfile:
                copyfileobj(response.raw, imgfile)
        else:
            _LOGGER.error("Cannot write image to file, response %s",
                          response.status_code)

    def video_to_file(self, path):
        """Write video to file.

        :param path: Path to write file
        """
        _LOGGER.debug("Writing video from %s to %s", self.name, path)
        response = self._cached_video
        with open(path, 'wb') as vidfile:
            copyfileobj(response.raw, vidfile)
