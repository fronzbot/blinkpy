"""Defines Blink cameras."""

import copy
import string
import os
import logging
import datetime
from json import dumps
import traceback
import aiohttp
from aiofiles import open
from requests.compat import urljoin
from blinkpy import api
from blinkpy.helpers.constants import TIMEOUT_MEDIA
from blinkpy.helpers.util import to_alphanumeric

_LOGGER = logging.getLogger(__name__)


class BlinkCamera:
    """Class to initialize individual camera."""

    def __init__(self, sync):
        """Initialize BlinkCamera."""
        self.sync = sync
        self.name = None
        self.camera_id = None
        self.network_id = None
        self.thumbnail = None
        self.serial = None
        self._version = None
        self.motion_enabled = None
        self.battery_level = None
        self._battery_voltage = None
        self.clip = None
        # A clip remains in the recent clips list until is has
        # been downloaded or has been expired.
        self.recent_clips = []
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
        self.sync_signal_strength = None

    @property
    def attributes(self):
        """Return dictionary of all camera attributes."""
        attributes = {
            "name": self.name,
            "camera_id": self.camera_id,
            "serial": self.serial,
            "version": self._version,
            "temperature": self.temperature,
            "temperature_c": self.temperature_c,
            "temperature_calibrated": self.temperature_calibrated,
            "battery": self.battery,
            "battery_level": self.battery_level,
            "battery_voltage": self._battery_voltage,
            "thumbnail": self.thumbnail,
            "video": self.clip,
            "recent_clips": self.recent_clips,
            "motion_enabled": self.motion_enabled,
            "motion_detected": self.motion_detected,
            "wifi_strength": self.wifi_strength,
            "network_id": self.sync.network_id,
            "sync_module": self.sync.name,
            "sync_signal_strength": self.sync_signal_strength,
            "last_record": self.last_record,
            "type": self.product_type,
        }
        return attributes

    @property
    def battery(self):
        """Return battery as string."""
        return self.battery_state

    @property
    def battery_voltage(self):
        """Return battery voltage as a number in 100ths of volts, so 165 = 1.65v."""
        return self._battery_voltage

    @property
    def temperature_c(self):
        """Return temperature in celsius."""
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
    def version(self):
        """Return the camera Firmware version."""
        return self._version

    @property
    def arm(self):
        """Return arm status of camera."""
        return self.motion_enabled

    async def async_arm(self, value):
        """Set camera arm status."""
        if value:
            return await api.request_motion_detection_enable(
                self.sync.blink, self.network_id, self.camera_id
            )
        return await api.request_motion_detection_disable(
            self.sync.blink, self.network_id, self.camera_id
        )

    @property
    async def night_vision(self):
        """Return night_vision status."""
        res = await api.request_get_config(
            self.sync.blink,
            self.network_id,
            self.camera_id,
            product_type=self.product_type,
        )
        if res is None:
            return None
        if self.product_type == "catalina":
            res = res.get("camera", [{}])[0]
        if res["illuminator_enable"] in [0, 1, 2]:
            res["illuminator_enable"] = ["off", "on", "auto"][
                res.get("illuminator_enable")
            ]
        nv_keys = [
            "night_vision_control",
            "illuminator_enable",
            "illuminator_enable_v2",
        ]
        return {key: res.get(key) for key in nv_keys}

    async def async_set_night_vision(self, value):
        """Set camera night_vision status."""
        if value not in ["on", "off", "auto"]:
            return None
        if self.product_type == "catalina":
            value = {"off": 0, "on": 1, "auto": 2}.get(value, None)
        data = dumps({"illuminator_enable": value})
        res = await api.request_update_config(
            self.sync.blink,
            self.network_id,
            self.camera_id,
            product_type=self.product_type,
            data=data,
        )
        if res and res.status == 200:
            return await res.json()
        return None

    async def record(self):
        """Initiate clip recording."""
        return await api.request_new_video(
            self.sync.blink, self.network_id, self.camera_id
        )

    async def get_media(self, media_type="image") -> aiohttp.ClientRequest:
        """Download media (image or video)."""
        if media_type.lower() == "video":
            return await self.get_video_clip()
        return await self.get_thumbnail()

    async def get_thumbnail(self, url=None):
        """Download thumbnail image."""
        if not url:
            url = self.thumbnail
            if not url:
                _LOGGER.warning("Thumbnail URL not available: self.thumbnail=%s", url)
                return None
        return await api.http_get(
            self.sync.blink,
            url=url,
            stream=True,
            json=False,
            timeout=TIMEOUT_MEDIA,
        )

    async def get_video_clip(self, url=None):
        """Download video clip."""
        if not url:
            url = self.clip
            if not url:
                _LOGGER.warning("Video clip URL not available: self.clip=%s", url)
                return None
        return await api.http_get(
            self.sync.blink,
            url=url,
            stream=True,
            json=False,
            timeout=TIMEOUT_MEDIA,
        )

    async def snap_picture(self):
        """Take a picture with camera to create a new thumbnail."""
        ret_val = await api.request_new_image(
            self.sync.blink, self.network_id, self.camera_id
        )
        response = await self.get_media()
        if response and response.status == 200:
            self._cached_image = await response.read()

        return ret_val

    async def set_motion_detect(self, enable):
        """Set motion detection."""
        _LOGGER.warning(
            "Method is deprecated as of v0.16.0 and will be removed in "
            "a future version. Please use the BlinkCamera.arm property instead."
        )
        if enable:
            return await api.request_motion_detection_enable(
                self.sync.blink, self.network_id, self.camera_id
            )
        return await api.request_motion_detection_disable(
            self.sync.blink, self.network_id, self.camera_id
        )

    async def update(self, config, force_cache=False, expire_clips=True, **kwargs):
        """Update camera info."""
        if bool(config):
            self.extract_config_info(config)
            await self.get_sensor_info()
            await self.update_images(
                config, force_cache=force_cache, expire_clips=expire_clips
            )

    def extract_config_info(self, config):
        """Extract info from config."""
        self.name = config.get("name", "unknown")
        self.camera_id = str(config.get("id", "unknown"))
        self.network_id = str(config.get("network_id", "unknown"))
        self.serial = config.get("serial")
        self._version = config.get("fw_version")
        self.motion_enabled = config.get("enabled", "unknown")
        self._battery_voltage = config.get("battery_voltage", None)
        self.battery_state = config.get("battery_state") or config.get("battery")
        self.wifi_strength = config.get("wifi_strength")
        if signals := config.get("signals"):
            self.battery_level = signals.get("battery")
            self.sync_signal_strength = signals.get("lfr")
            self.temperature = signals.get("temp")
        else:
            self.temperature = config.get("temperature")
        self.product_type = config.get("type")

    async def get_sensor_info(self):
        """Retrieve calibrated temperature from special endpoint."""
        resp = await api.request_camera_sensors(
            self.sync.blink, self.network_id, self.camera_id
        )
        try:
            self.temperature_calibrated = resp["temp"]
        except (TypeError, KeyError):
            self.temperature_calibrated = self.temperature
            _LOGGER.warning(
                "Could not retrieve calibrated temperature response %s.", resp
            )
            _LOGGER.warning(
                "for network_id (%s) and camera_id (%s)",
                self.network_id,
                self.camera_id,
            )

    async def update_images(self, config, force_cache=False, expire_clips=True):
        """Update images for camera."""
        new_thumbnail = None
        thumb_addr = None
        thumb_string = None
        if config.get("thumbnail", False):
            thumb_addr = config["thumbnail"]
            try:
                # API update only returns the timestamp!
                int(thumb_addr)
                thumb_string = (
                    "/api/v3/media/accounts/"
                    f"{self.sync.blink.account_id}/networks/"
                    f"{self.network_id}/{self.product_type}/"
                    f"{self.camera_id}/thumbnail/"
                    f"thumbnail.jpg?ts={thumb_addr}&ext="
                )
            except ValueError:
                # This is the old API and has the full url
                thumb_string = f"{thumb_addr}.jpg"
                # Check that new full api url has not been returned:
                if thumb_addr.endswith("&ext="):
                    thumb_string = thumb_addr

            if thumb_string is not None:
                new_thumbnail = urljoin(self.sync.urls.base_url, thumb_string)

        else:
            _LOGGER.warning("Could not find thumbnail for camera %s.", self.name)

        try:
            self.motion_detected = self.sync.motion[self.name]
        except KeyError:
            self.motion_detected = False

        clip_addr = None
        try:

            def timesort(record):
                rec_time = record["time"]
                iso_time = datetime.datetime.fromisoformat(rec_time)
                stamp = int(iso_time.timestamp())
                return stamp

            if (
                len(self.sync.last_records) > 0
                and len(self.sync.last_records[self.name]) > 0
            ):
                last_records = sorted(self.sync.last_records[self.name], key=timesort)
                for rec in last_records:
                    clip_addr = rec["clip"]
                    self.clip = f"{self.sync.urls.base_url}{clip_addr}"
                    self.last_record = rec["time"]
                    if self.motion_detected:
                        recent = {"time": self.last_record, "clip": self.clip}
                        # Prevent duplicates.
                        if recent not in self.recent_clips:
                            self.recent_clips.append(recent)
                if len(self.recent_clips) > 0:
                    _LOGGER.debug(
                        "Found %s recent clips for %s",
                        len(self.recent_clips),
                        self.name,
                    )
                    _LOGGER.debug(
                        "Most recent clip for %s was created at %s : %s",
                        self.name,
                        self.last_record,
                        self.clip,
                    )
        except (KeyError, IndexError):
            ex = traceback.format_exc()
            trace = "".join(traceback.format_stack())
            _LOGGER.error("Error getting last records for '%s': %s", self.name, ex)
            _LOGGER.debug("\n%s", trace)

        # If the thumbnail or clip have changed, update the cache
        update_cached_image = False
        if new_thumbnail != self.thumbnail or self._cached_image is None:
            update_cached_image = True
        self.thumbnail = new_thumbnail

        update_cached_video = False
        if self._cached_video is None or self.motion_detected:
            update_cached_video = True

        if new_thumbnail is not None and (update_cached_image or force_cache):
            response = await self.get_media()
            if response and response.status == 200:
                self._cached_image = await response.read()

        if clip_addr is not None and (update_cached_video or force_cache):
            response = await self.get_media(media_type="video")
            if response and response.status == 200:
                self._cached_video = await response.read()

        # Don't let the recent clips list grow without bound.
        if expire_clips:
            await self.expire_recent_clips()

    async def expire_recent_clips(self, delta=datetime.timedelta(hours=1)):
        """Remove recent clips from list when they get too old."""
        to_keep = []
        for clip in self.recent_clips:
            timedelta = (datetime.datetime.now() - delta).timestamp()
            clip_time = datetime.datetime.fromisoformat(clip["time"]).timestamp()
            if clip_time > timedelta:
                to_keep.append(clip)
        num_expired = len(self.recent_clips) - len(to_keep)
        if num_expired > 0:
            _LOGGER.info("Expired %s clips from '%s'", num_expired, self.name)
        self.recent_clips = copy.deepcopy(to_keep)
        if len(self.recent_clips) > 0:
            _LOGGER.info(
                "'%s' has %s clips available for download",
                self.name,
                len(self.recent_clips),
            )
            for clip in self.recent_clips:
                url = clip["clip"]
                if "local_storage" in url:
                    await api.http_post(self.sync.blink, url)

    async def get_liveview(self):
        """Get liveview rtsps link."""
        response = await api.request_camera_liveview(
            self.sync.blink, self.sync.network_id, self.camera_id
        )
        return response["server"]

    async def image_to_file(self, path):
        """
        Write image to file.

        :param path: Path to write file
        """
        _LOGGER.debug("Writing image from %s to %s", self.name, path)
        response = await self.get_media()
        if response and response.status == 200:
            async with open(path, "wb") as imagefile:
                await imagefile.write(await response.read())
        else:
            _LOGGER.error("Cannot write image to file, response %s", response.status)

    async def video_to_file(self, path):
        """
        Write video to file.

        :param path: Path to write file
        """
        _LOGGER.debug("Writing video from %s to %s", self.name, path)
        response = await self.get_media(media_type="video")
        if response is None:
            _LOGGER.error("No saved video exists for %s.", self.name)
            return
        async with open(path, "wb") as vidfile:
            await vidfile.write(await response.read())

    async def save_recent_clips(
        self, output_dir="/tmp", file_pattern="${created}_${name}.mp4"
    ):
        """Save all recent clips using timestamp file name pattern."""
        if output_dir[-1] != "/":
            output_dir += "/"

        recent = copy.deepcopy(self.recent_clips)

        num_saved = 0
        for clip in recent:
            clip_time = datetime.datetime.fromisoformat(clip["time"])
            clip_time_local = clip_time.replace(
                tzinfo=datetime.timezone.utc
            ).astimezone(tz=None)
            created_at = clip_time_local.strftime("%Y%m%d_%H%M%S")
            clip_addr = clip["clip"]

            file_name = string.Template(file_pattern).substitute(
                created=created_at, name=to_alphanumeric(self.name)
            )
            path = os.path.join(output_dir, file_name)
            _LOGGER.debug("Saving %s to %s", clip_addr, path)
            media = await self.get_video_clip(clip_addr)
            if media and media.status == 200:
                async with open(path, "wb") as clip_file:
                    await clip_file.write(await media.read())
                num_saved += 1
                try:
                    # Remove recent clip from the list once the download has finished.
                    self.recent_clips.remove(clip)
                    _LOGGER.debug("Removed %s from recent clips", clip)
                except ValueError:
                    ex = traceback.format_exc()
                    _LOGGER.error("Error removing clip from list: %s", ex)
                    trace = "".join(traceback.format_stack())
                    _LOGGER.debug("\n%s", trace)

        if len(recent) == 0:
            _LOGGER.info("No recent clips to save for '%s'.", self.name)
        else:
            _LOGGER.info(
                "Saved %s of %s recent clips from '%s' to directory %s",
                num_saved,
                len(recent),
                self.name,
                output_dir,
            )


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

    async def async_arm(self, value):
        """Set camera arm status."""
        url = (
            f"{self.sync.urls.base_url}/api/v1/accounts/"
            f"{self.sync.blink.account_id}/networks/"
            f"{self.network_id}/owls/{self.camera_id}/config"
        )
        data = dumps({"enabled": value})
        response = await api.http_post(self.sync.blink, url, data=data)
        await api.wait_for_command(self.sync.blink, response)
        return response

    async def snap_picture(self):
        """Snap picture for a blink mini camera."""
        url = (
            f"{self.sync.urls.base_url}/api/v1/accounts/"
            f"{self.sync.blink.account_id}/networks/"
            f"{self.network_id}/owls/{self.camera_id}/thumbnail"
        )
        response = await api.http_post(self.sync.blink, url)
        await api.wait_for_command(self.sync.blink, response)
        return response

    async def get_sensor_info(self):
        """Get sensor info for blink mini camera."""

    async def get_liveview(self):
        """Get liveview link."""
        url = (
            f"{self.sync.urls.base_url}/api/v1/accounts/"
            f"{self.sync.blink.account_id}/networks/"
            f"{self.network_id}/owls/{self.camera_id}/liveview"
        )
        response = await api.http_post(self.sync.blink, url)
        await api.wait_for_command(self.sync.blink, response)
        server = response["server"]
        server_split = server.split(":")
        server_split[0] = "rtsps"
        link = ":".join(server_split)
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
        return self.motion_enabled

    async def async_arm(self, value):
        """Set camera arm status."""
        url = (
            f"{self.sync.urls.base_url}/api/v1/accounts/"
            f"{self.sync.blink.account_id}/networks/"
            f"{self.sync.network_id}/doorbells/{self.camera_id}"
        )
        if value:
            url = f"{url}/enable"
        else:
            url = f"{url}/disable"

        response = await api.http_post(self.sync.blink, url)
        await api.wait_for_command(self.sync.blink, response)
        return response

    async def snap_picture(self):
        """Snap picture for a blink doorbell camera."""
        url = (
            f"{self.sync.urls.base_url}/api/v1/accounts/"
            f"{self.sync.blink.account_id}/networks/"
            f"{self.sync.network_id}/doorbells/{self.camera_id}/thumbnail"
        )

        response = await api.http_post(self.sync.blink, url)
        await api.wait_for_command(self.sync.blink, response)
        return response

    async def get_sensor_info(self):
        """Get sensor info for blink doorbell camera."""

    async def get_liveview(self):
        """Get liveview link."""
        url = (
            f"{self.sync.urls.base_url}/api/v1/accounts/"
            f"{self.sync.blink.account_id}/networks/"
            f"{self.sync.network_id}/doorbells/{self.camera_id}/liveview"
        )
        response = await api.http_post(self.sync.blink, url)
        await api.wait_for_command(self.sync.blink, response)
        server = response["server"]
        link = server.replace("immis://", "rtsps://")
        return link
