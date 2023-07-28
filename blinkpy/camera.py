"""Defines Blink cameras."""
from __future__ import annotations
from typing import TYPE_CHECKING
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

if TYPE_CHECKING:
    from blinkpy.sync_module import BlinkSyncModule

_LOGGER = logging.getLogger(__name__)


class BlinkCamera:
    """Class to initialize individual camera."""

    def __init__(self, sync: BlinkSyncModule):
        """Initiailize BlinkCamera."""
        self.sync: BlinkSyncModule = sync
        self.name: str = ""
        self.camera_id: str = ""
        self.network_id: str = ""
        self.thumbnail: str | None = None
        self.serial: str = ""
        self.motion_enabled: bool = False
        self.battery_voltage: float | None = None
        self.clip: str = ""
        # A clip remains in the recent clips list until is has been downloaded or has been expired.
        self.recent_clips: list = []
        self.temperature: float | None = None
        self.temperature_calibrated: float | None = None
        self.battery_state: bool | None = None
        self.motion_detected: bool | None = None
        self.wifi_strength = None
        self.last_record = None
        self._cached_image: bytes | None = None
        self._cached_video: bytes | None = None
        self.camera_type: str = ""
        self.product_type : str = ""

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
            "recent_clips": self.recent_clips,
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
    def battery(self) -> bool | None:
        """Return battery as string."""
        return self.battery_state

    @property
    def temperature_c(self) -> float | None:
        """Return temperature in celcius."""
        return round((self.temperature - 32) / 9.0 * 5.0, 1) if self.temperature is not None else None    

    @property
    def image_from_cache(self):
        """Return the most recently cached image."""
        return self._cached_image if self._cached_image else None
            
    @property
    def video_from_cache(self):
        """Return the most recently cached video."""
        if self._cached_video:
            return self._cached_video
        return None

    @property
    def arm(self) -> bool | None:
        """Return arm status of camera."""
        return self.motion_enabled

    async def async_arm(self, value: bool) -> aiohttp.ClientResponse | None:
        """Set camera arm status."""
        if value:
            return await api.request_motion_detection_enable(
                self.sync.blink, self.network_id, self.camera_id
            )
        return await api.request_motion_detection_disable(
            self.sync.blink, self.network_id, self.camera_id
        )

    @property
    async def night_vision(self) -> dict | None:
        """Return night_vision status."""
        res = await api.request_get_config(
            self.sync.blink,
            self.network_id,
            self.camera_id,
            product_type=self.product_type,
        )
        if res is None:
            return None
        assert isinstance (res,dict)
        if self.product_type == "catalina":
             res_json = res.get("camera", [{}])[0]
        if res_json["illuminator_enable"] in [0, 1, 2]:
            index: int = res_json["illuminator_enable"] 
            res_json["illuminator_enable"] = ["off", "on", "auto"][index]
        nv_keys : list = [
            "night_vision_control",
            "illuminator_enable",
            "illuminator_enable_v2",
        ]
        return {key: res_json.get(key) for key in nv_keys}

    async def async_set_night_vision(self, value: str) -> str | None:
        """Set camera night_vision status."""
        if value not in ["on", "off", "auto"]:
            return None
        if self.product_type == "catalina":
            data = dumps({"illuminator_enable": {"off": 0, "on": 1, "auto": 2}.get(value)})
            res = await api.request_update_config(
                self.sync.blink,
                self.network_id,
                self.camera_id,
                product_type=self.product_type,
                data=data,
            )
            assert isinstance(res,aiohttp.ClientResponse)
            if res and res.status == 200:
                return await res.json()
        return None

    async def record(self) -> aiohttp.ClientResponse:
        """Initiate clip recording."""
        return await api.request_new_video(
            self.sync.blink, self.network_id, self.camera_id
        )

    async def get_media(self, media_type="image") -> aiohttp.ClientResponse | None:
        """Download media (image or video)."""
        if media_type.lower() == "video":
            return await self.get_video_clip()
        return await self.get_thumbnail()

    async def get_thumbnail(self, url: str | None = None) -> aiohttp.ClientResponse | None:
        """Download thumbnail image."""
        if not url:
            url = self.thumbnail
            if not url:
                _LOGGER.warning(f"Thumbnail URL not available: self.thumbnail={url}")
                return None
        resp = await api.http_get(
            self.sync.blink,
            url=url,
            stream=True,
            json=False,
            timeout=TIMEOUT_MEDIA,
        )
        return resp


    async def get_video_clip(self, url: str | None = None) -> aiohttp.ClientResponse | None:
        """Download video clip."""
        if not url:
            url = self.clip
            if not url:
                _LOGGER.warning(f"Video clip URL not available: self.clip={url}")
                return None
        resp = await api.http_get(
            self.sync.blink,
            url=url,
            stream=True,
            json=False,
            timeout=TIMEOUT_MEDIA,
        )
        if isinstance(resp, aiohttp.ClientResponse):
            return resp
        return None
    
    async def snap_picture(self) -> aiohttp.ClientResponse | None:
        """Take a picture with camera to create a new thumbnail."""
        return await api.request_new_image(
            self.sync.blink, self.network_id, self.camera_id
        )

    async def set_motion_detect(self, enable: bool) -> aiohttp.ClientResponse | None:
        """Set motion detection."""
        _LOGGER.warning(
            "Method is deprecated as of v0.16.0 and will be removed in a future version. Please use the BlinkCamera.arm property instead."
        )
        if enable:
            return await api.request_motion_detection_enable(
                self.sync.blink, self.network_id, self.camera_id
            )
        return await api.request_motion_detection_disable(
            self.sync.blink, self.network_id, self.camera_id
        )

    async def update(
        self,
        config: dict,
        force_cache: bool = False,
        expire_clips: bool = True,
        **kwargs,
    ):
        """Update camera info."""
        if config != {}:
            self.extract_config_info(config)
            await self.get_sensor_info()
            await self.update_images(
                config, force_cache=force_cache, expire_clips=expire_clips
            )

    def extract_config_info(self, config: dict) -> None:
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

    async def get_sensor_info(self) -> None:
        """Retrieve calibrated temperatue from special endpoint."""
        resp = await api.request_camera_sensors(
            self.sync.blink, self.network_id, self.camera_id
        )
        try:
            self.temperature_calibrated = resp["temp"] # type: ignore
        except (TypeError, KeyError):
            self.temperature_calibrated = self.temperature
            _LOGGER.warning("Could not retrieve calibrated temperature.")

    async def update_images(
        self, config: dict, force_cache: bool = False, expire_clips: bool = True
    ) -> None:
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

            if thumb_string is not None:
                new_thumbnail = urljoin(self.sync.urls.base_url, thumb_string)

        else:
            _LOGGER.warning("Could not find thumbnail for camera %s", self.name)

        try:
            self.motion_detected = self.sync.motion[self.name] # type: ignore
        except KeyError:
            self.motion_detected = False

        clip_addr = None
        try:

            def timest(record):
                rec_time = record["time"]
                iso_time = datetime.datetime.fromisoformat(rec_time)
                stamp = int(iso_time.timestamp())
                return stamp

            if (
                len(self.sync.last_records) > 0
                and len(self.sync.last_records[self.name]) > 0
            ):
                last_records = sorted(self.sync.last_records[self.name], key=timest)
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
                        f"Found {len(self.recent_clips)} recent clips for {self.name}"
                    )
                    _LOGGER.debug(
                        f"Most recent clip for {self.name} was created at {self.last_record}: {self.clip}"
                    )
        except (KeyError, IndexError):
            ex = traceback.format_exc()
            trace = "".join(traceback.format_stack())
            _LOGGER.error(f"Error getting last records for '{self.name}': {ex}")
            _LOGGER.debug(f"\n{trace}")

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

    async def expire_recent_clips(
        self, delta: datetime.timedelta = datetime.timedelta(hours=1)
    ) -> None:
        """Remove recent clips from list when they get too old."""
        to_keep = []
        for clip in self.recent_clips:
            timedelta = (datetime.datetime.now() - delta).timestamp()
            clip_time = datetime.datetime.fromisoformat(clip["time"]).timestamp()
            if clip_time > timedelta:
                to_keep.append(clip)
        num_expired = len(self.recent_clips) - len(to_keep)
        if num_expired > 0:
            _LOGGER.info(f"Expired {num_expired} clips from '{self.name}'")
        self.recent_clips = copy.deepcopy(to_keep)
        if len(self.recent_clips) > 0:
            _LOGGER.info(
                f"'{self.name}' has {len(self.recent_clips)} clips available for download"
            )
            for clip in self.recent_clips:
                url = clip["clip"]
                if "local_storage" in url:
                    await api.http_post(self.sync.blink, url)

    async def get_liveview(self) -> str | None:
        """Get livewview rtsps link."""
        response = await api.request_camera_liveview(
            self.sync.blink, self.sync.network_id, self.camera_id
        )
        if response:
            assert isinstance(response,aiohttp.ClientResponse)
            json_response = await response.json()
            if json_response:
                return json_response["server"]
        return None
    
    async def image_to_file(self, path: str) -> None:
        """
        Write image to file.

        :param path: Path to write file
        """
        _LOGGER.debug("Writing image from %s to %s", self.name, path)
        response = await self.get_media()
        if response and response.status == 200:
            async with open(path, "wb") as imgfile:
                await imgfile.write(await response.read())
        elif response:
            _LOGGER.error("Cannot write image to file, response %s", response.status)
        else:
            _LOGGER.error("Cannot write image to file, No response")

    async def video_to_file(self, path: str) -> None:
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
        self, output_dir: str = "/tmp", file_pattern: str = "${created}_${name}.mp4"
    ) -> None:
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
            _LOGGER.debug(f"Saving {clip_addr} to {path}")
            media = await self.get_video_clip(clip_addr)
            if media and media.status == 200:
                async with open(path, "wb") as clip_file:
                    await clip_file.write(await media.read())
                num_saved += 1
                try:
                    # Remove recent clip from the list once the download has finished.
                    self.recent_clips.remove(clip)
                    _LOGGER.debug(f"Removed {clip} from recent clips")
                except ValueError:
                    ex = traceback.format_exc()
                    _LOGGER.error(f"Error removing clip from list: {ex}")
                    trace = "".join(traceback.format_stack())
                    _LOGGER.debug(f"\n{trace}")

        if len(recent) == 0:
            _LOGGER.info(f"No recent clips to save for '{self.name}'.")
        else:
            _LOGGER.info(
                f"Saved {num_saved} of {len(recent)} recent clips from '{self.name}' to directory {output_dir}"
            )


class BlinkCameraMini(BlinkCamera):
    """Define a class for a Blink Mini camera."""

    def __init__(self, sync: BlinkSyncModule) -> None:
        """Initialize a Blink Mini cameras."""
        super().__init__(sync)
        self.camera_type = "mini"

    @property
    def arm(self) -> bool | None:
        """Return camera arm status."""
        return self.sync.arm

    async def async_arm(self, value: bool) -> aiohttp.ClientResponse | None:
        """Set camera arm status."""
        url = f"{self.sync.urls.base_url}/api/v1/accounts/{self.sync.blink.account_id}/networks/{self.network_id}/owls/{self.camera_id}/config"
        data = dumps({"enabled": value})
        resp = await api.http_post(self.sync.blink, url, json=False, data=data)
        if isinstance(resp,aiohttp.ClientResponse):
            return resp
        return None

    async def snap_picture(self) -> aiohttp.ClientResponse | None:
        """Snap picture for a blink mini camera."""
        url = f"{self.sync.urls.base_url}/api/v1/accounts/{self.sync.blink.account_id}/networks/{self.network_id}/owls/{self.camera_id}/thumbnail"
        resp = await api.http_post(self.sync.blink, url)
        if isinstance(resp,aiohttp.ClientResponse):
            return resp
        return None
    
    async def get_sensor_info(self) -> None:
        """Get sensor info for blink mini camera."""

    async def get_liveview(self) -> str:
        """Get liveview link."""
        url = f"{self.sync.urls.base_url}/api/v1/accounts/{self.sync.blink.account_id}/networks/{self.network_id}/owls/{self.camera_id}/liveview"
        response = await api.http_post(self.sync.blink, url)
        if response:
            if isinstance(response, aiohttp.ClientResponse):
                json_response = await response.json()
                if json_response:
                    server = json_response["server"]
                    server_split = server.split(":")
                    server_split[0] = "rtsps:"
                    link = "".join(server_split)
                    return link
        return ""


class BlinkDoorbell(BlinkCamera):
    """Define a class for a Blink Doorbell camera."""

    def __init__(self, sync: BlinkSyncModule):
        """Initialize a Blink Doorbell."""
        super().__init__(sync)
        self.camera_type: str = "doorbell"

    @property
    def arm(self) -> bool:
        """Return camera arm status."""
        return self.motion_enabled

    async def async_arm(self, value: bool) -> aiohttp.ClientResponse | None:
        """Set camera arm status."""
        url = f"{self.sync.urls.base_url}/api/v1/accounts/{self.sync.blink.account_id}/networks/{self.sync.network_id}/doorbells/{self.camera_id}"
        if value:
            url = f"{url}/enable"
        else:
            url = f"{url}/disable"
        response = await api.http_post(self.sync.blink, url)
        if isinstance(response,aiohttp.ClientResponse):
            return response
        return None
    
    async def snap_picture(self) -> aiohttp.ClientResponse | None:
        """Snap picture for a blink doorbell camera."""
        url = f"{self.sync.urls.base_url}/api/v1/accounts/{self.sync.blink.account_id}/networks/{self.sync.network_id}/doorbells/{self.camera_id}/thumbnail"
        response = await api.http_post(self.sync.blink, url)
        if isinstance(response,aiohttp.ClientResponse):
            return response
        return None

    async def get_sensor_info(self) -> None:
        """Get sensor info for blink doorbell camera."""

    async def get_liveview(self) -> str:
        """Get liveview link."""
        url = f"{self.sync.urls.base_url}/api/v1/accounts/{self.sync.blink.account_id}/networks/{self.sync.network_id}/doorbells/{self.camera_id}/liveview"
        response = await api.http_post(self.sync.blink, url)
        if response:
            if isinstance(response,aiohttp.ClientResponse):
                json_response = await response.json()
                if json_response:
                    server = json_response["server"]
                    link = server.replace("immis://", "rtsps://")
                    return link
        return ""
