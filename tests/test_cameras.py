"""
Test all camera attributes.

Tests the camera initialization and attributes of
individual BlinkCamera instantiations once the
Blink system is set up.
"""

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

    @mock.patch(
        "blinkpy.api.request_motion_detection_enable",
        mock.AsyncMock(return_value="enable"),
    )
    @mock.patch(
        "blinkpy.api.request_motion_detection_disable",
        mock.AsyncMock(return_value="disable"),
    )
    async def test_camera_arm_status(self, mock_resp):
        """Test arming and disarming camera."""
        self.camera.motion_enabled = None
        await self.camera.async_arm(None)
        self.assertFalse(self.camera.arm)
        await self.camera.async_arm(False)
        self.camera.motion_enabled = False
        self.assertFalse(self.camera.arm)
        await self.camera.async_arm(True)
        self.camera.motion_enabled = True
        self.assertTrue(self.camera.arm)

        self.camera = BlinkCameraMini(self.blink.sync["test"])
        self.camera.motion_enabled = None
        await self.camera.async_arm(None)
        self.assertFalse(self.camera.arm)

    async def test_doorbell_camera_arm(self, mock_resp):
        """Test arming and disarming camera."""
        self.blink.sync.arm = False
        doorbell_camera = BlinkDoorbell(self.blink.sync["test"])
        doorbell_camera.motion_enabled = None
        await doorbell_camera.async_arm(None)
        self.assertFalse(doorbell_camera.arm)
        await doorbell_camera.async_arm(False)
        doorbell_camera.motion_enabled = False
        self.assertFalse(doorbell_camera.arm)
        await doorbell_camera.async_arm(True)
        doorbell_camera.motion_enabled = True
        self.assertTrue(doorbell_camera.arm)

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
            if key == "recent_clips":
                self.assertEqual(attr[key], [])
                continue
            self.assertEqual(attr[key], None)

    def test_doorbell_missing_attributes(self, mock_resp):
        """Test that attributes return None if missing."""
        camera = BlinkDoorbell(self.blink.sync)
        self.blink.sync.network_id = None
        self.blink.sync.name = None
        attr = camera.attributes
        for key in attr:
            if key == "recent_clips":
                self.assertEqual(attr[key], [])
                continue
            self.assertEqual(attr[key], None)

    async def test_camera_stream(self, mock_resp):
        """Test that camera stream returns correct url."""
        mock_resp.return_value = {"server": "rtsps://foo.bar"}
        mini_camera = BlinkCameraMini(self.blink.sync["test"])
        doorbell_camera = BlinkDoorbell(self.blink.sync["test"])
        self.assertEqual(await self.camera.get_liveview(), "rtsps://foo.bar")
        self.assertEqual(await mini_camera.get_liveview(), "rtsps://foo.bar")
        self.assertEqual(await doorbell_camera.get_liveview(), "rtsps://foo.bar")

    async def test_different_thumb_api(self, mock_resp):
        """Test that the correct url is created with new api."""
        thumb_endpoint = "https://rest-test.immedia-semi.com/api/v3/media/accounts/9999/networks/5678/test/1234/thumbnail/thumbnail.jpg?ts=1357924680&ext="
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
            "thumbnail": 1357924680,
            "type": "test",
        }
        mock_resp.side_effect = [
            {"temp": 71},
            mresp.MockResponse({"test": 200}, 200, raw_data="test"),
        ]
        self.camera.sync.blink.account_id = 9999
        await self.camera.update(config, expire_clips=False)
        self.assertEqual(self.camera.thumbnail, thumb_endpoint)

    async def test_thumb_return_none(self, mock_resp):
        """Test that a 'None" thumbnail is doesn't break system."""
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
            "thumbnail": None,
            "type": "test",
        }
        mock_resp.side_effect = [
            {"temp": 71},
            "test",
        ]
        await self.camera.update(config, expire_clips=False)
        self.assertEqual(self.camera.thumbnail, None)

    async def test_new_thumb_url_returned(self, mock_resp):
        """Test that thumb handled properly if new url returned."""
        thumb_return = "/api/v3/media/accounts/9999/networks/5678/test/1234/thumbnail/thumbnail.jpg?ts=1357924680&ext="
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
            "thumbnail": thumb_return,
            "type": "test",
        }
        mock_resp.side_effect = [
            {"temp": 71},
            mresp.MockResponse({"test": 200}, 200, raw_data="test"),
        ]
        self.camera.sync.blink.account_id = 9999
        await self.camera.update(config, expire_clips=False)
        self.assertEqual(
            self.camera.thumbnail, f"https://rest-test.immedia-semi.com{thumb_return}"
        )
