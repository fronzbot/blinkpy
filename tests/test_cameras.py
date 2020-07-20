"""
Test all camera attributes.

Tests the camera initialization and attributes of
individual BlinkCamera instantiations once the
Blink system is set up.
"""

import unittest
from unittest import mock
from blinkpy.blinkpy import Blink
from blinkpy.helpers.util import BlinkURLHandler
from blinkpy.sync_module import BlinkSyncModule
from blinkpy.camera import BlinkCamera, BlinkCameraMini


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
class TestBlinkCameraSetup(unittest.TestCase):
    """Test the Blink class in blinkpy."""

    def setUp(self):
        """Set up Blink module."""
        self.blink = Blink()
        self.blink.urls = BlinkURLHandler("test")
        self.blink.sync["test"] = BlinkSyncModule(self.blink, "test", 1234, [])
        self.camera = BlinkCamera(self.blink.sync["test"])
        self.camera.name = "foobar"
        self.blink.sync["test"].cameras["foobar"] = self.camera

    def tearDown(self):
        """Clean up after test."""
        self.blink = None
        self.camera = None

    def test_camera_update(self, mock_resp):
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
        self.camera.sync.last_record = {
            "new": {"clip": "/test.mp4", "time": "1970-01-01T00:00:00"}
        }
        mock_resp.side_effect = [
            {"temp": 71},
            "test",
            "foobar",
        ]
        self.camera.update(config)
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

    def test_no_thumbnails(self, mock_resp):
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
            self.camera.update(config, force=True)
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

    def test_no_video_clips(self, mock_resp):
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
        self.camera.sync.homescreen = {"devices": []}
        self.camera.update(config, force_cache=True)
        self.assertEqual(self.camera.clip, None)
        self.assertEqual(self.camera.video_from_cache, None)

    def test_camera_arm_status(self, mock_resp):
        """Test arming and disarming camera."""
        self.camera.motion_enabled = None
        self.assertFalse(self.camera.arm)
        self.camera.motion_enabled = False
        self.assertFalse(self.camera.arm)
        self.camera.motion_enabled = True
        self.assertTrue(self.camera.arm)

    @mock.patch("blinkpy.camera.api.request_motion_detection_enable")
    @mock.patch("blinkpy.camera.api.request_motion_detection_disable")
    def test_motion_detection_enable_disable(self, mock_dis, mock_en, mock_rep):
        """Test setting motion detection enable properly."""
        mock_dis.return_value = "disable"
        mock_en.return_value = "enable"
        self.assertEqual(self.camera.set_motion_detect(True), "enable")
        self.assertEqual(self.camera.set_motion_detect(False), "disable")

    def test_missing_attributes(self, mock_resp):
        """Test that attributes return None if missing."""
        self.camera.temperature = None
        self.camera.serial = None
        attr = self.camera.attributes
        self.assertEqual(attr["serial"], None)
        self.assertEqual(attr["temperature"], None)
        self.assertEqual(attr["temperature_c"], None)

    def test_mini_missing_attributes(self, mock_resp):
        """Test that attributes return None if missing."""
        camera = BlinkCameraMini(self.blink.sync)
        self.blink.sync.network_id = None
        self.blink.sync.name = None
        attr = camera.attributes
        for key in attr:
            self.assertEqual(attr[key], None)
