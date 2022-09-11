"""Defines Blink cameras."""

from shutil import copyfileobj
import logging
from json import dumps
from requests.compat import urljoin
from blinkpy import api
from blinkpy.helpers.constants import TIMEOUT_MEDIA

_LOGGER = logging.getLogger(__name__)


class BlinkCamera:
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
        self.temperature_calibrated = None
        self.battery_state = None
        self.motion_detected = None
        self.wifi_strength = None
        self.last_record = None
        self._cached_image = None
        self._cached_video = None
        self.camera_type = ""
        self.product_type = None

    @property
    def attributes(self):
        """Return dictionary of all camera attributes."""
        attributes = {
            "name": self.name,
            "camera_id": self.camera_id,
            "serial": self.serial,
            "temperature": self.temperature,
            "temperature_c": self.temperature_c,
            "temperature_calibrated": self.temperature_calibrated,
            "battery": self.battery,
            "battery_voltage": self.battery_voltage,
            "thumbnail": self.thumbnail,
            "video": self.clip,
            "motion_enabled": self.motion_enabled,
            "motion_detected": self.motion_detected,
            "wifi_strength": self.wifi_strength,
            "network_id": self.sync.network_id,
            "sync_module": self.sync.name,
            "last_record": self.last_record,
            "type": self.product_type,
        }
        return attributes

    @property
    def battery(self):
        """Return battery as string."""
        return self.battery_state

    @property
    def temperature_c(self):
        """Return temperature in celcius."""
        try:
            return round((self.temperature - 32) / 9.0 * 5.0, 1)
        except TypeError:
            return None

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

    @property
    def arm(self):
        """Return arm status of camera."""
        return self.motion_enabled

    @arm.setter
    def arm(self, value):
        """Set camera arm status."""
        if value:
            return api.request_motion_detection_enable(
                self.sync.blink, self.network_id, self.camera_id
            )
        return api.request_motion_detection_disable(
            self.sync.blink, self.network_id, self.camera_id
        )

    def record(self):
        """Initiate clip recording."""
        return api.request_new_video(self.sync.blink, self.network_id, self.camera_id)

    def get_media(self, media_type="image"):
        """Download media (image or video)."""
        url = self.thumbnail
        if media_type.lower() == "video":
            url = self.clip
        return api.http_get(
            self.sync.blink,
            url=url,
            stream=True,
            json=False,
            timeout=TIMEOUT_MEDIA,
        )

    def snap_picture(self):
        """Take a picture with camera to create a new thumbnail."""
        return api.request_new_image(self.sync.blink, self.network_id, self.camera_id)

    def set_motion_detect(self, enable):
        """Set motion detection."""
        _LOGGER.warning(
            "Method is deprecated as of v0.16.0 and will be removed in a future version. Please use the BlinkCamera.arm property instead."
        )
        if enable:
            return api.request_motion_detection_enable(
                self.sync.blink, self.network_id, self.camera_id
            )
        return api.request_motion_detection_disable(
            self.sync.blink, self.network_id, self.camera_id
        )

    def update(self, config, force_cache=False, **kwargs):
        """Update camera info."""
        self.extract_config_info(config)
        self.get_sensor_info()
        self.update_images(config, force_cache=force_cache)

    def extract_config_info(self, config):
        """Extract info from config."""
        self.name = config.get("name", "unknown")
        self.camera_id = str(config.get("id", "unknown"))
        self.network_id = str(config.get("network_id", "unknown"))
        self.serial = config.get("serial", None)
        self.motion_enabled = config.get("enabled", "unknown")
        self.battery_voltage = config.get("battery_voltage", None)
        self.battery_state = config.get("battery_state", None) or config.get(
            "battery", None
        )
        self.temperature = config.get("temperature", None)
        self.wifi_strength = config.get("wifi_strength", None)
        self.product_type = config.get("type", None)

    def get_sensor_info(self):
        """Retrieve calibrated temperatue from special endpoint."""
        resp = api.request_camera_sensors(
            self.sync.blink, self.network_id, self.camera_id
        )
        try:
            self.temperature_calibrated = resp["temp"]
        except (TypeError, KeyError):
            self.temperature_calibrated = self.temperature
            _LOGGER.warning("Could not retrieve calibrated temperature.")

    def update_images(self, config, force_cache=False):
        """Update images for camera."""
        new_thumbnail = None
        thumb_addr = None
        thumb_string = None
        if config.get("thumbnail", False):
            thumb_addr = config["thumbnail"]
            try:
                # API update only returns the timestamp!
                int(thumb_addr)
                thumb_string = f"/api/v3/media/accounts/{self.sync.blink.account_id}/networks/{self.network_id}/{self.product_type}/{self.camera_id}/thumbnail/thumbnail.jpg?ts={thumb_addr}&ext="
            except ValueError:
                # This is the old API and has the full url
                thumb_string = f"{thumb_addr}.jpg"
                # Check that new full api url has not been returned:
                if thumb_addr.endswith("&ext="):
                    thumb_string = thumb_addr
            except TypeError:
                # Thumb address is None
                pass

            if thumb_string is not None:
                new_thumbnail = urljoin(self.sync.urls.base_url, thumb_string)

        else:
            _LOGGER.warning("Could not find thumbnail for camera %s", self.name)

        try:
            self.motion_detected = self.sync.motion[self.name]
        except KeyError:
            self.motion_detected = False

        clip_addr = None
        try:
            clip_addr = self.sync.last_record[self.name]["clip"]
            self.last_record = self.sync.last_record[self.name]["time"]
            self.clip = f"{self.sync.urls.base_url}{clip_addr}"
        except KeyError:
            pass

        # If the thumbnail or clip have changed, update the cache
        update_cached_image = False
        if new_thumbnail != self.thumbnail or self._cached_image is None:
            update_cached_image = True
        self.thumbnail = new_thumbnail

        update_cached_video = False
        if self._cached_video is None or self.motion_detected:
            update_cached_video = True

        if new_thumbnail is not None and (update_cached_image or force_cache):
            self._cached_image = self.get_media()

        if clip_addr is not None and (update_cached_video or force_cache):
            self._cached_video = self.get_media(media_type="video")

    def get_liveview(self):
        """Get livewview rtsps link."""
        response = api.request_camera_liveview(
            self.sync.blink, self.sync.network_id, self.camera_id
        )
        return response["server"]

    def image_to_file(self, path):
        """
        Write image to file.

        :param path: Path to write file
        """
        _LOGGER.debug("Writing image from %s to %s", self.name, path)
        response = self.get_media()
        if response.status_code == 200:
            with open(path, "wb") as imgfile:
                copyfileobj(response.raw, imgfile)
        else:
            _LOGGER.error(
                "Cannot write image to file, response %s", response.status_code
            )

    def video_to_file(self, path):
        """
        Write video to file.

        :param path: Path to write file
        """
        _LOGGER.debug("Writing video from %s to %s", self.name, path)
        response = self.get_media(media_type="video")
        if response is None:
            _LOGGER.error("No saved video exist for %s.", self.name)
            return
        with open(path, "wb") as vidfile:
            copyfileobj(response.raw, vidfile)


class BlinkCameraMini(BlinkCamera):
    """Define a class for a Blink Mini camera."""

    def __init__(self, sync):
        """Initialize a Blink Mini cameras."""
        super().__init__(sync)
        self.camera_type = "mini"

    @property
    def arm(self):
        """Return camera arm status."""
        return self.sync.arm

    @arm.setter
    def arm(self, value):
        """Set camera arm status."""
        url = f"{self.sync.urls.base_url}/api/v1/accounts/{self.sync.blink.account_id}/networks/{self.network_id}/owls/{self.camera_id}/config"
        data = dumps({"enabled": value})
        return api.http_post(self.sync.blink, url, json=False, data=data)

    def snap_picture(self):
        """Snap picture for a blink mini camera."""
        url = f"{self.sync.urls.base_url}/api/v1/accounts/{self.sync.blink.account_id}/networks/{self.network_id}/owls/{self.camera_id}/thumbnail"
        return api.http_post(self.sync.blink, url)

    def get_sensor_info(self):
        """Get sensor info for blink mini camera."""

    def get_liveview(self):
        """Get liveview link."""
        url = f"{self.sync.urls.base_url}/api/v1/accounts/{self.sync.blink.account_id}/networks/{self.network_id}/owls/{self.camera_id}/liveview"
        response = api.http_post(self.sync.blink, url)
        server = response["server"]
        server_split = server.split(":")
        server_split[0] = "rtsps:"
        link = "".join(server_split)
        return link


class BlinkDoorbell(BlinkCamera):
    """Define a class for a Blink Doorbell camera."""

    def __init__(self, sync):
        """Initialize a Blink Doorbell."""
        super().__init__(sync)
        self.camera_type = "doorbell"

    @property
    def arm(self):
        """Return camera arm status."""
        return self.sync.arm

    @arm.setter
    def arm(self, value):
        """Set camera arm status."""
        _LOGGER.warning(
            "Individual camera motion detection enable/disable for Blink Doorbell is unsupported at this time."
        )

    def snap_picture(self):
        """Snap picture for a blink doorbell camera."""
        url = f"{self.sync.urls.base_url}/api/v1/accounts/{self.sync.blink.account_id}/networks/{self.sync.network_id}/doorbells/{self.camera_id}/thumbnail"
        return api.http_post(self.sync.blink, url)

    def get_sensor_info(self):
        """Get sensor info for blink doorbell camera."""

    def get_liveview(self):
        """Get liveview link."""
        url = f"{self.sync.urls.base_url}/api/v1/accounts/{self.sync.blink.account_id}/networks/{self.sync.network_id}/doorbells/{self.camera_id}/liveview"
        response = api.http_post(self.sync.blink, url)
        server = response["server"]
        link = server.replace("immis://", "rtsps://")
        return link
