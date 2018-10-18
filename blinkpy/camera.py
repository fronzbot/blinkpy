"""Defines Blink cameras."""

from shutil import copyfileobj
import logging
from blinkpy import api

_LOGGER = logging.getLogger(__name__)

MAX_CLIPS = 5


class BlinkCamera():
    """Class to initialize individual camera."""

    def __init__(self, sync):
        """Initiailize BlinkCamera."""
        self.sync = sync
        self.name = None
        self.camera_id = None
        self.network_id = None
        self.thumbnail = None
        self.serial = None
        self.motion_enabled = None
        self.battery_voltage = None
        self.clip = None
        self.temperature = None
        self.battery_state = None
        self.motion_detected = None
        self.wifi_strength = None
        self.last_record = []
        self._cached_image = None
        self._cached_video = None

    @property
    def attributes(self):
        """Return dictionary of all camera attributes."""
        attributes = {
            'name': self.name,
            'camera_id': self.camera_id,
            'serial': self.serial,
            'temperature': self.temperature,
            'temperature_c': self.temperature_c,
            'battery': self.battery,
            'thumbnail': self.thumbnail,
            'video': self.clip,
            'motion_enabled': self.motion_enabled,
            'motion_detected': self.motion_detected,
            'wifi_strength': self.wifi_strength,
            'network_id': self.sync.network_id,
            'last_record': self.last_record
        }
        return attributes

    @property
    def battery(self):
        """Return battery level as percentage."""
        return round(self.battery_voltage / 180 * 100)

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
        return api.request_new_image(self.sync.blink,
                                     self.network_id,
                                     self.camera_id)

    def set_motion_detect(self, enable):
        """Set motion detection."""
        if enable:
            return api.request_motion_detection_enable(self.sync.blink,
                                                       self.network_id,
                                                       self.camera_id)
        return api.request_motion_detection_disable(self.sync.blink,
                                                    self.network_id,
                                                    self.camera_id)

    def update(self, config, force_cache=False):
        """Update camera info."""
        self.name = config['name']
        self.camera_id = str(config['camera_id'])
        self.network_id = str(config['network_id'])
        self.serial = config['serial']
        self.motion_enabled = config['enabled']
        self.battery_voltage = config['battery_voltage']
        self.battery_state = config['battery_state']
        self.temperature = config['temperature']
        self.wifi_strength = config['wifi_strength']

        # Check if thumbnail exists in config, if not try to
        # get it from the homescreen info in teh sync module
        # otherwise set it to None and log an error
        new_thumbnail = None
        if config['thumbnail']:
            thumb_addr = config['thumbnail']
        else:
            thumb_addr = self.get_thumb_from_homescreen()

        if thumb_addr is not None:
            new_thumbnail = "{}{}.jpg".format(self.sync.urls.base_url,
                                              thumb_addr)

        # Check if a new motion clip has been recorded
        # check_for_motion_method sets motion_detected variable
        self.check_for_motion()
        clip_addr = None
        if self.last_record:
            clip_addr = self.sync.all_clips[self.name][self.last_record[0]]
            self.clip = "{}{}".format(self.sync.urls.base_url,
                                      clip_addr)

        # If the thumbnail or clip have changed, update the cache
        update_cached_image = False
        if new_thumbnail != self.thumbnail or self._cached_image is None:
            update_cached_image = True
        self.thumbnail = new_thumbnail

        update_cached_video = False
        if self._cached_video is None or self.motion_detected:
            update_cached_video = True

        if new_thumbnail is not None and (update_cached_image or force_cache):
            self._cached_image = api.http_get(self.sync.blink,
                                              url=self.thumbnail,
                                              stream=True,
                                              json=False)
        if clip_addr is not None and (update_cached_video or force_cache):
            self._cached_video = api.http_get(self.sync.blink,
                                              url=self.clip,
                                              stream=True,
                                              json=False)

    def check_for_motion(self):
        """Check if motion detected.."""
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
            _LOGGER.info("Could not extract clip info from camera %s",
                         self.name)

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
        if response is None:
            _LOGGER.error("No saved video exist for %s.", self.name)
            return
        with open(path, 'wb') as vidfile:
            copyfileobj(response.raw, vidfile)

    def get_thumb_from_homescreen(self):
        """Retrieve thumbnail from homescreen."""
        for device in self.sync.homescreen['devices']:
            try:
                device_type = device['device_type']
                device_name = device['name']
                device_thumb = device['thumbnail']
                if device_type == 'camera' and device_name == self.name:
                    return device_thumb
            except KeyError:
                pass
        _LOGGER.error("Could not find thumbnail for camera %s", self.name)
        return None
