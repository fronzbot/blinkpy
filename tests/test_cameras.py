"""
Test all camera attributes.

Tests the camera initialization and attributes of
individual BlinkCamera instantiations once the
Blink system is set up.
"""

import importlib
from unittest import mock
from unittest import IsolatedAsyncioTestCase
import pytest

import blinkpy.api
from blinkpy.blinkpy import Blink
from blinkpy.sync_module import BlinkSyncModule
from blinkpy.camera import BlinkCamera, BlinkCameraMini, BlinkDoorbell
from blinkpy.livestream import BlinkLiveStream
from blinkpy.helpers import util

import tests.mock_responses as mresp

CONFIG = {
    "name": "new",
    "id": 1234,
    "network_id": 5678,
    "serial": "12345678",
    "enabled": False,
    "battery_state": "ok",
    "temperature": 68,
    "thumbnail": 1357924680,
    "signals": {"lfr": 5, "wifi": 4, "battery": 3},
    "type": "test",
}


def mock_throttle(*args, **kwargs):
    """Mock class for Throttle decorator."""

    def decorator(func):
        return func

    return decorator


@mock.patch("blinkpy.auth.Auth.query", return_value={})
class TestBlinkCameraSetup(IsolatedAsyncioTestCase):
    """Test the Blink class in blinkpy."""

    def setUp(self):
        """Set up Blink module."""
        self.throttle_patch = mock.patch("blinkpy.api.Throttle", mock_throttle)
        self.throttle_patch.start()

        importlib.reload(blinkpy.api)

        self.blink = Blink(session=mock.AsyncMock())
        self.blink.urls = util.BlinkURLHandler("test")
        self.blink.sync["test"] = BlinkSyncModule(self.blink, "test", 1234, [])
        self.camera = BlinkCamera(self.blink.sync["test"])
        self.camera.name = "foobar"
        self.mini_camera = BlinkCameraMini(self.blink.sync["test"])
        self.doorbell = BlinkDoorbell(self.blink.sync["test"])

        self.blink.sync["test"].cameras["foobar"] = self.camera

    def tearDown(self):
        """Clean up after test."""
        self.blink = None
        self.camera = None
        self.mini_camera = None
        self.doorbell = None
        self.throttle_patch.stop()

    async def test_camera_arm_disarm(self, mock_resp):
        """Test base camera arm and disarm."""
        with mock.patch(
            "blinkpy.api.wait_for_command", new_callable=mock.AsyncMock
        ) as mock_wait:
            mock_resp.side_effect = ["arm", "disarm"]
            mock_wait.side_effect = [True, True]
            self.assertEqual(await self.camera.async_arm(True), "arm")
            self.assertEqual(await self.camera.async_arm(False), "disarm")

    async def test_mini_camera_arm_disarm(self, mock_resp):
        """Test mini camera arm and disarm."""
        with mock.patch(
            "blinkpy.api.wait_for_command", new_callable=mock.AsyncMock
        ) as mock_wait:
            mock_resp.side_effect = ["arm", "disarm"]
            mock_wait.return_value = [True, True]
            self.assertEqual(await self.mini_camera.async_arm(True), "arm")
            self.assertEqual(await self.mini_camera.async_arm(False), "disarm")

    async def test_doorbell_arm_disarm(self, mock_resp):
        """Test doorbell arm and disarm."""
        with mock.patch(
            "blinkpy.api.wait_for_command", new_callable=mock.AsyncMock
        ) as mock_wait:
            mock_resp.side_effect = ["arm", "disarm"]
            mock_wait.side_effect = [True, True]
            self.assertEqual(await self.doorbell.async_arm(True), "arm")
            self.assertEqual(await self.doorbell.async_arm(False), "disarm")

    def test_missing_attributes(self, mock_resp):
        """Test that attributes return None if missing."""
        self.camera.temperature = None
        self.camera.serial = None
        self.camera._version = None
        attr = self.camera.attributes
        self.assertEqual(attr["serial"], None)
        self.assertEqual(attr["temperature"], None)
        self.assertEqual(attr["temperature_c"], None)
        self.assertEqual(attr["version"], None)
        self.assertEqual(self.camera.version, None)

    def test_mini_missing_attributes(self, mock_resp):
        """Test that attributes return None if missing."""
        self.mini_camera = BlinkCameraMini(self.blink.sync)
        self.blink.sync.network_id = None
        self.blink.sync.name = None
        attr = self.mini_camera.attributes
        for key in attr:
            if key == "recent_clips":
                self.assertEqual(attr[key], [])
                continue
            self.assertEqual(attr[key], None)

    def test_doorbell_missing_attributes(self, mock_resp):
        """Test that attributes return None if missing."""
        self.doorbell = BlinkDoorbell(self.blink.sync)
        self.blink.sync.network_id = None
        self.blink.sync.name = None
        attr = self.doorbell.attributes
        for key in attr:
            if key == "recent_clips":
                self.assertEqual(attr[key], [])
                continue
            self.assertEqual(attr[key], None)

    async def test_camera_stream(self, mock_resp):
        """Test that camera stream returns correct url."""
        mock_resp.return_value = {"server": "rtsps://foo.bar"}
        self.assertEqual(await self.camera.get_liveview(), "rtsps://foo.bar")
        self.assertEqual(await self.mini_camera.get_liveview(), "rtsps://foo.bar")
        self.assertEqual(await self.doorbell.get_liveview(), "rtsps://foo.bar")
        with pytest.raises(NotImplementedError):
            await self.camera.init_livestream()
        with pytest.raises(NotImplementedError):
            await self.mini_camera.init_livestream()
        with pytest.raises(NotImplementedError):
            await self.doorbell.init_livestream()

    async def test_camera_livestream(self, mock_resp):
        """Test that camera livestream returns correct object."""
        mock_resp.return_value = {
            "command_id": 1234567890,
            "join_available": True,
            "join_state": "available",
            "server": "immis://1.2.3.4:443/ABCDEFGHIJKMLNOP__IMDS_1234567812345678?client_id=123",
            "duration": 300,
            "extended_duration": 5400,
            "continue_interval": 300,
            "continue_warning": 0,
            "polling_interval": 15,
            "submit_logs": True,
            "new_command": True,
            "media_id": None,
            "options": {"poor_connection": False},
            "liveview_token": "abcdefghijklmnopqrstuv",
        }
        self.assertIsInstance(await self.camera.init_livestream(), BlinkLiveStream)
        self.assertIsInstance(await self.mini_camera.init_livestream(), BlinkLiveStream)
        self.assertIsInstance(await self.doorbell.init_livestream(), BlinkLiveStream)

    async def test_different_thumb_api(self, mock_resp):
        """Test that the correct url is created with new api."""
        thumb_endpoint = "https://rest-test.immedia-semi.com/api/v3/media/accounts/9999/networks/5678/test/1234/thumbnail/thumbnail.jpg?ts=1357924680&ext="
        mock_resp.side_effect = [
            {"temp": 71},
            mresp.MockResponse({"test": 200}, 200, raw_data="test"),
        ]
        self.camera.sync.blink.auth.account_id = 9999
        await self.camera.update(CONFIG, expire_clips=False)
        self.assertEqual(self.camera.thumbnail, thumb_endpoint)

    async def test_thumb_return_none(self, mock_resp):
        """Test that a 'None" thumbnail is doesn't break system."""
        config = {
            **CONFIG,
            **{
                "thumbnail": None,
            },
        }
        mock_resp.side_effect = [
            {"temp": 71},
            "test",
        ]
        await self.camera.update(config, expire_clips=False)
        self.assertEqual(self.camera.thumbnail, None)

    async def test_new_thumb_url_returned(self, mock_resp):
        """Test that thumb handled properly if new url returned."""
        thumb_return = (
            "/api/v3/media/accounts/9999/networks/5678/"
            "test/1234/thumbnail/thumbnail.jpg?ts=1357924680&ext="
        )
        config = {
            **CONFIG,
            **{
                "thumbnail": thumb_return,
            },
        }
        mock_resp.side_effect = [
            {"temp": 71},
            mresp.MockResponse({"test": 200}, 200, raw_data="test"),
        ]
        self.camera.sync.blink.auth.account_id = 9999
        await self.camera.update(config, expire_clips=False)
        self.assertEqual(
            self.camera.thumbnail, f"https://rest-test.immedia-semi.com{thumb_return}"
        )
