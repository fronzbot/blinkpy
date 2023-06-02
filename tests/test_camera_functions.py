"""
Test all camera attributes.

Tests the camera initialization and attributes of
individual BlinkCamera instantiations once the
Blink system is set up.
"""

import datetime
from unittest import mock
from unittest import IsolatedAsyncioTestCase
from blinkpy.blinkpy import Blink
from blinkpy.helpers.util import BlinkURLHandler
from blinkpy.sync_module import BlinkSyncModule
from blinkpy.camera import BlinkCamera, BlinkCameraMini, BlinkDoorbell
import tests.mock_responses as mresp

CAMERA_CFG = {
    "camera": [
        {
            "battery_voltage": 90,
            "motion_alert": True,
            "wifi_strength": -30,
            "temperature": 68,
        }
    ]
}


@mock.patch("blinkpy.auth.Auth.query")
class TestBlinkCameraSetup(IsolatedAsyncioTestCase):
    """Test the Blink class in blinkpy."""

    def setUp(self):
        """Set up Blink module."""
        self.blink = Blink(session=mock.AsyncMock())
        self.blink.urls = BlinkURLHandler("test")
        self.blink.sync["test"] = BlinkSyncModule(self.blink, "test", 1234, [])
        self.camera = BlinkCamera(self.blink.sync["test"])
        self.camera.name = "foobar"
        self.blink.sync["test"].cameras["foobar"] = self.camera

    def tearDown(self):
        """Clean up after test."""
        self.blink = None
        self.camera = None

    async def test_camera_update(self, mock_resp):
        """Test that we can properly update camera properties."""
        config = {
            "name": "new",
            "id": 1234,
            "network_id": 5678,
            "serial": "12345678",
            "enabled": False,
            "battery_voltage": 90,
            "battery_state": "ok",
            "temperature": 68,
            "wifi_strength": 4,
            "thumbnail": "/thumb",
        }
        self.camera.last_record = ["1"]
        self.camera.sync.last_records = {
            "new": [{"clip": "/test.mp4", "time": "1970-01-01T00:00:00"}]
        }
        mock_resp.side_effect = [
            {"temp": 71},
            mresp.MockResponse({"test": 200}, 200, raw_data="test"),
            mresp.MockResponse({"foobar": 200}, 200, raw_data="foobar"),
        ]
        self.assertIsNone(self.camera.image_from_cache)

        await self.camera.update(config, expire_clips=False)
        self.assertEqual(self.camera.name, "new")
        self.assertEqual(self.camera.camera_id, "1234")
        self.assertEqual(self.camera.network_id, "5678")
        self.assertEqual(self.camera.serial, "12345678")
        self.assertEqual(self.camera.motion_enabled, False)
        self.assertEqual(self.camera.battery, "ok")
        self.assertEqual(self.camera.temperature, 68)
        self.assertEqual(self.camera.temperature_c, 20)
        self.assertEqual(self.camera.temperature_calibrated, 71)
        self.assertEqual(self.camera.wifi_strength, 4)
        self.assertEqual(
            self.camera.thumbnail, "https://rest-test.immedia-semi.com/thumb.jpg"
        )
        self.assertEqual(
            self.camera.clip, "https://rest-test.immedia-semi.com/test.mp4"
        )
        self.assertEqual(self.camera.image_from_cache, "test")
        self.assertEqual(self.camera.video_from_cache, "foobar")

        # Check that thumbnail without slash processed properly
        mock_resp.side_effect = [
            mresp.MockResponse({"test": 200}, 200, raw_data="thumb_no_slash")
        ]
        await self.camera.update_images(
            {"thumbnail": "thumb_no_slash"}, expire_clips=False
        )
        self.assertEqual(
            self.camera.thumbnail,
            "https://rest-test.immedia-semi.com/thumb_no_slash.jpg",
        )

    async def test_no_thumbnails(self, mock_resp):
        """Tests that thumbnail is 'None' if none found."""
        mock_resp.return_value = "foobar"
        self.camera.last_record = ["1"]
        config = {
            "name": "new",
            "id": 1234,
            "network_id": 5678,
            "serial": "12345678",
            "enabled": False,
            "battery_voltage": 90,
            "battery_state": "ok",
            "temperature": 68,
            "wifi_strength": 4,
            "thumbnail": "",
        }
        self.camera.sync.homescreen = {"devices": []}
        self.assertEqual(self.camera.temperature_calibrated, None)
        with self.assertLogs() as logrecord:
            await self.camera.update(config, force=True, expire_clips=False)
        self.assertEqual(self.camera.thumbnail, None)
        self.assertEqual(self.camera.last_record, ["1"])
        self.assertEqual(self.camera.temperature_calibrated, 68)
        self.assertEqual(
            logrecord.output,
            [
                (
                    "WARNING:blinkpy.camera:Could not retrieve calibrated "
                    "temperature."
                ),
                ("WARNING:blinkpy.camera:Could not find thumbnail for camera new"),
            ],
        )

    async def test_no_video_clips(self, mock_resp):
        """Tests that we still proceed with camera setup with no videos."""
        mock_resp.return_value = "foobar"
        config = {
            "name": "new",
            "id": 1234,
            "network_id": 5678,
            "serial": "12345678",
            "enabled": False,
            "battery_voltage": 90,
            "battery_state": "ok",
            "temperature": 68,
            "wifi_strength": 4,
            "thumbnail": "/foobar",
        }
        mock_resp.return_value = mresp.MockResponse({"test": 200}, 200, raw_data="")
        self.camera.sync.homescreen = {"devices": []}
        await self.camera.update(config, force_cache=True, expire_clips=False)
        self.assertEqual(self.camera.clip, None)
        self.assertEqual(self.camera.video_from_cache, None)

    async def test_recent_video_clips(self, mock_resp):
        """Tests that the last records in the sync module are added to the camera recent clips list."""
        config = {
            "name": "new",
            "id": 1234,
            "network_id": 5678,
            "serial": "12345678",
            "enabled": False,
            "battery_voltage": 90,
            "battery_state": "ok",
            "temperature": 68,
            "wifi_strength": 4,
            "thumbnail": "/thumb",
        }
        self.camera.sync.last_records["foobar"] = []
        record2 = {"clip": "/clip2", "time": "2022-12-01 00:00:10+00:00"}
        self.camera.sync.last_records["foobar"].append(record2)
        record1 = {"clip": "/clip1", "time": "2022-12-01 00:00:00+00:00"}
        self.camera.sync.last_records["foobar"].append(record1)
        self.camera.sync.motion["foobar"] = True
        await self.camera.update_images(config, expire_clips=False)
        record1["clip"] = self.blink.urls.base_url + "/clip1"
        record2["clip"] = self.blink.urls.base_url + "/clip2"
        self.assertEqual(self.camera.recent_clips[0], record1)
        self.assertEqual(self.camera.recent_clips[1], record2)

    async def test_recent_video_clips_missing_key(self, mock_resp):
        """Tests that the missing key failst."""
        config = {
            "name": "new",
            "id": 1234,
            "network_id": 5678,
            "serial": "12345678",
            "enabled": False,
            "battery_voltage": 90,
            "battery_state": "ok",
            "temperature": 68,
            "wifi_strength": 4,
            "thumbnail": "/thumb",
        }
        self.camera.sync.last_records["foobar"] = []
        record2 = {"clip": "/clip2"}
        self.camera.sync.last_records["foobar"].append(record2)
        self.camera.sync.motion["foobar"] = True

        with self.assertLogs(level="ERROR") as dl_log:
            await self.camera.update_images(config, expire_clips=False)

        self.assertIsNotNone(dl_log.output)

    async def test_expire_recent_clips(self, mock_resp):
        """Test expiration of recent clips."""
        self.camera.recent_clips = []
        now = datetime.datetime.now()
        self.camera.recent_clips.append(
            {
                "time": (now - datetime.timedelta(minutes=20)).isoformat(),
                "clip": "/clip1",
            },
        )
        self.camera.recent_clips.append(
            {
                "time": (now - datetime.timedelta(minutes=1)).isoformat(),
                "clip": "local_storage/clip2",
            },
        )
        await self.camera.expire_recent_clips(delta=datetime.timedelta(minutes=5))
        self.assertEqual(len(self.camera.recent_clips), 1)

    @mock.patch(
        "blinkpy.api.request_motion_detection_enable",
        mock.AsyncMock(return_value="enable"),
    )
    @mock.patch(
        "blinkpy.api.request_motion_detection_disable",
        mock.AsyncMock(return_value="disable"),
    )
    async def test_motion_detection_enable_disable(self, mock_rep):
        """Test setting motion detection enable properly."""
        self.assertEqual(await self.camera.set_motion_detect(True), "enable")
        self.assertEqual(await self.camera.set_motion_detect(False), "disable")

    async def test_night_vision(self, mock_resp):
        """Test Night Vision Camera functions."""
        # MJK - I don't know what the "real" response is supposed to look like
        # Need to confirm and adjust this test to match reality?
        mock_resp.return_value = "blah"
        self.assertIsNone(await self.camera.night_vision)

        self.camera.product_type = "catalina"
        mock_resp.return_value = {"camera": [{"name": "123", "illuminator_enable": 1}]}
        self.assertIsNotNone(await self.camera.night_vision)

        self.assertIsNone(await self.camera.async_set_night_vision("0"))

        mock_resp.return_value = mresp.MockResponse({"code": 200}, 200)
        self.assertIsNotNone(await self.camera.async_set_night_vision("on"))

        mock_resp.return_value = mresp.MockResponse({"code": 400}, 400)
        self.assertIsNone(await self.camera.async_set_night_vision("on"))

    async def test_record(self, mock_resp):
        """Test camera record function."""
        with mock.patch(
            "blinkpy.api.request_new_video", mock.AsyncMock(return_value=True)
        ):
            self.assertTrue(await self.camera.record())

        with mock.patch(
            "blinkpy.api.request_new_video", mock.AsyncMock(return_value=False)
        ):
            self.assertFalse(await self.camera.record())

    async def test_get_thumbnail(self, mock_resp):
        """Test get thumbnail without URL."""
        self.assertIsNone(await self.camera.get_thumbnail())

    async def test_get_video(self, mock_resp):
        """Test get video clip without URL."""
        self.assertIsNone(await self.camera.get_video_clip())

    @mock.patch(
        "blinkpy.api.request_new_image", mock.AsyncMock(return_value={"json": "Data"})
    )
    async def test_snap_picture(self, mock_resp):
        """Test camera snap picture function."""
        self.assertIsNotNone(await self.camera.snap_picture())

    @mock.patch("blinkpy.api.http_post", mock.AsyncMock(return_value={"json": "Data"}))
    async def test_snap_picture_blinkmini(self, mock_resp):
        """Test camera snap picture function."""
        self.camera = BlinkCameraMini(self.blink.sync["test"])
        self.assertIsNotNone(await self.camera.snap_picture())

    @mock.patch("blinkpy.api.http_post", mock.AsyncMock(return_value={"json": "Data"}))
    async def test_snap_picture_blinkdoorbell(self, mock_resp):
        """Test camera snap picture function."""
        self.camera = BlinkDoorbell(self.blink.sync["test"])
        self.assertIsNotNone(await self.camera.snap_picture())

    @mock.patch("blinkpy.camera.open", create=True)
    async def test_image_to_file(self, mock_open, mock_resp):
        """Test camera image to file."""
        mock_resp.return_value = mresp.MockResponse({}, 200, raw_data="raw data")
        self.camera.thumbnail = "/thumbnail"
        await self.camera.image_to_file("my_path")

    @mock.patch("blinkpy.camera.open", create=True)
    async def test_image_to_file_error(self, mock_open, mock_resp):
        """Test camera image to file with error."""
        mock_resp.return_value = mresp.MockResponse({}, 400, raw_data="raw data")
        self.camera.thumbnail = "/thumbnail"
        with self.assertLogs(level="DEBUG") as dl_log:
            await self.camera.image_to_file("my_path")
        self.assertEquals(
            dl_log.output[2],
            "ERROR:blinkpy.camera:Cannot write image to file, response 400",
        )

    @mock.patch("blinkpy.camera.open", create=True)
    async def test_video_to_file_none_response(self, mock_open, mock_resp):
        """Test camera video to file."""
        mock_resp.return_value = mresp.MockResponse({}, 200, raw_data="raw data")
        with self.assertLogs(level="DEBUG") as dl_log:
            await self.camera.video_to_file("my_path")
        self.assertEqual(
            dl_log.output[2],
            f"ERROR:blinkpy.camera:No saved video exists for {self.camera.name}.",
        )

    @mock.patch("blinkpy.camera.open", create=True)
    async def test_video_to_file(self, mock_open, mock_resp):
        """Test camera vido to file with error."""
        mock_resp.return_value = mresp.MockResponse({}, 400, raw_data="raw data")
        self.camera.clip = "my_clip"
        await self.camera.video_to_file("my_path")
        mock_open.assert_called_once()

    @mock.patch("blinkpy.camera.open", create=True)
    @mock.patch("blinkpy.camera.BlinkCamera.get_video_clip")
    async def test_save_recent_clips(self, mock_clip, mock_open, mock_resp):
        """Test camera save recent clips."""
        with self.assertLogs(level="DEBUG") as dl_log:
            await self.camera.save_recent_clips()
        self.assertEqual(
            dl_log.output[0],
            f"INFO:blinkpy.camera:No recent clips to save for '{self.camera.name}'.",
        )
        assert mock_open.call_count == 0

        self.camera.recent_clips = []
        now = datetime.datetime.now()
        self.camera.recent_clips.append(
            {
                "time": (now - datetime.timedelta(minutes=20)).isoformat(),
                "clip": "/clip1",
            },
        )
        self.camera.recent_clips.append(
            {
                "time": (now - datetime.timedelta(minutes=1)).isoformat(),
                "clip": "local_storage/clip2",
            },
        )
        mock_clip.return_value = mresp.MockResponse({}, 200, raw_data="raw data")
        with self.assertLogs(level="DEBUG") as dl_log:
            await self.camera.save_recent_clips()
        self.assertEqual(
            dl_log.output[4],
            f"INFO:blinkpy.camera:Saved 2 of 2 recent clips from '{self.camera.name}' to directory /tmp/",
        )
        assert mock_open.call_count == 2
