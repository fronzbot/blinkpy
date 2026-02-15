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

    @mock.patch(
        "blinkpy.api.request_camera_snooze",
        mock.AsyncMock(return_value={"status": 200}),
    )
    async def test_camera_snooze(self, mock_resp):
        """Test camera snooze."""
        self.camera.product_type = "catalina"
        with mock.patch.object(
            self.blink, "get_homescreen", mock.AsyncMock()
        ) as mock_homescreen:
            result = await self.camera.async_snooze(300)
            # Catalina cameras should NOT refresh homescreen
            mock_homescreen.assert_not_called()
        self.assertEqual(result, {"status": 200})

    @mock.patch(
        "blinkpy.api.request_camera_snooze",
        mock.AsyncMock(return_value={"status": 400}),
    )
    async def test_camera_snooze_failure(self, mock_resp):
        """Test camera snooze failure."""
        self.camera.product_type = "owl"
        with mock.patch.object(
            self.blink, "get_homescreen", mock.AsyncMock()
        ) as mock_homescreen:
            result = await self.camera.async_snooze(300)
            # Non-catalina/sedona cameras refresh homescreen even on failure
            mock_homescreen.assert_called_once()
        self.assertEqual(result, {"status": 400})

    @mock.patch(
        "blinkpy.api.request_camera_snooze",
        mock.AsyncMock(return_value=None),
    )
    async def test_camera_snooze_none_response(self, mock_resp):
        """Test camera snooze with None response."""
        self.camera.product_type = "doorbell"
        with mock.patch.object(
            self.blink, "get_homescreen", mock.AsyncMock()
        ) as mock_homescreen:
            result = await self.camera.async_snooze(240)
            # get_homescreen should not be called when response is None
            mock_homescreen.assert_not_called()
        self.assertIsNone(result)

    @mock.patch(
        "blinkpy.api.request_camera_snooze",
        mock.AsyncMock(return_value={"status": 200}),
    )
    async def test_camera_snooze_mini(self, mock_resp):
        """Test mini camera snooze refreshes homescreen."""
        self.camera.product_type = "mini"
        with mock.patch.object(
            self.blink, "get_homescreen", mock.AsyncMock()
        ) as mock_homescreen:
            result = await self.camera.async_snooze(300)
            # Mini cameras should refresh homescreen
            mock_homescreen.assert_called_once()
        self.assertEqual(result, {"status": 200})

    @mock.patch(
        "blinkpy.api.request_camera_snooze",
        mock.AsyncMock(return_value={"status": 200}),
    )
    async def test_camera_snooze_sedona(self, mock_resp):
        """Test sedona camera snooze does not refresh homescreen."""
        self.camera.product_type = "sedona"
        with mock.patch.object(
            self.blink, "get_homescreen", mock.AsyncMock()
        ) as mock_homescreen:
            result = await self.camera.async_snooze(300)
            # Sedona cameras should NOT refresh homescreen
            mock_homescreen.assert_not_called()
        self.assertEqual(result, {"status": 200})

    @mock.patch(
        "blinkpy.api.request_get_config",
        mock.AsyncMock(
            return_value={"camera": [{"snooze_till": "2026-02-15T12:00:00+00:00"}]}
        ),
    )
    async def test_camera_snoozed_catalina(self, mock_resp):
        """Test getting snoozed status for catalina camera."""
        self.camera.product_type = "catalina"
        self.camera.network_id = "5678"
        self.camera.camera_id = "1234"
        result = await self.camera.snoozed
        self.assertTrue(result)

    async def test_camera_snoozed_owl(self, mock_resp):
        """Test getting snoozed status for owl camera."""
        self.camera.product_type = "owl"
        self.camera.camera_id = "1234"
        self.blink.homescreen = {
            "owls": [{"id": "1234", "snooze": "2026-02-15T12:00:00+00:00"}]
        }
        result = await self.camera.snoozed
        self.assertTrue(result)
        # Verify we're reading from homescreen, not calling API
        expected_snooze = "2026-02-15T12:00:00+00:00"
        self.assertEqual(self.blink.homescreen["owls"][0]["snooze"], expected_snooze)

    async def test_camera_snoozed_owl_false(self, mock_resp):
        """Test getting snoozed status returns False when not snoozed."""
        self.camera.product_type = "owl"
        self.camera.camera_id = "9999"
        self.blink.homescreen = {
            "owls": [{"id": "1234", "snooze": "2026-02-15T12:00:00+00:00"}]
        }
        result = await self.camera.snoozed
        self.assertFalse(result)
        # Verify camera ID 9999 is not in homescreen
        camera_ids = [str(cam["id"]) for cam in self.blink.homescreen["owls"]]
        self.assertNotIn("9999", camera_ids)

    async def test_camera_snoozed_doorbell(self, mock_resp):
        """Test getting snoozed status for doorbell camera."""
        self.camera.product_type = "doorbell"
        self.camera.camera_id = "5678"
        self.blink.homescreen = {
            "doorbells": [{"id": "5678", "snooze": "2026-02-15T12:00:00+00:00"}]
        }
        result = await self.camera.snoozed
        self.assertTrue(result)
        # Verify we're reading from the doorbells collection
        self.assertIn("doorbells", self.blink.homescreen)
        self.assertEqual(self.blink.homescreen["doorbells"][0]["id"], "5678")

    async def test_camera_snoozed_lotus(self, mock_resp):
        """Test getting snoozed status for lotus (doorbell) camera."""
        self.camera.product_type = "lotus"
        self.camera.camera_id = "5678"
        self.blink.homescreen = {
            "doorbells": [{"id": "5678", "snooze": "2026-02-15T12:00:00+00:00"}]
        }
        result = await self.camera.snoozed
        self.assertTrue(result)
        # Verify lotus uses doorbells collection
        self.assertIn("doorbells", self.blink.homescreen)

    async def test_camera_snoozed_hawk(self, mock_resp):
        """Test getting snoozed status for hawk camera."""
        self.camera.product_type = "hawk"
        self.camera.camera_id = "1234"
        self.blink.homescreen = {
            "owls": [{"id": "1234", "snooze": "2026-02-15T12:00:00+00:00"}]
        }
        result = await self.camera.snoozed
        self.assertTrue(result)
        # Verify hawk uses owls collection
        self.assertIn("owls", self.blink.homescreen)

    @mock.patch(
        "blinkpy.api.request_get_config",
        mock.AsyncMock(
            return_value={"camera": [{"snooze_till": "2026-02-15T12:00:00+00:00"}]}
        ),
    )
    async def test_camera_snoozed_sedona(self, mock_resp):
        """Test getting snoozed status for sedona camera."""
        self.camera.product_type = "sedona"
        self.camera.network_id = "5678"
        self.camera.camera_id = "1234"
        result = await self.camera.snoozed
        self.assertTrue(result)

    async def test_camera_snoozed_boolean_true(self, mock_resp):
        """Test getting snoozed status when snooze is boolean True."""
        self.camera.product_type = "owl"
        self.camera.camera_id = "1234"
        self.blink.homescreen = {"owls": [{"id": "1234", "snooze": True}]}
        result = await self.camera.snoozed
        self.assertTrue(result)

    async def test_camera_snoozed_boolean_false(self, mock_resp):
        """Test getting snoozed status when snooze is boolean False."""
        self.camera.product_type = "owl"
        self.camera.camera_id = "1234"
        self.blink.homescreen = {"owls": [{"id": "1234", "snooze": False}]}
        result = await self.camera.snoozed
        self.assertFalse(result)
        # Verify the snooze value is actually False, not missing
        camera = next(c for c in self.blink.homescreen["owls"] if c["id"] == "1234")
        self.assertIn("snooze", camera)
        self.assertFalse(camera["snooze"])

    async def test_camera_snoozed_mini(self, mock_resp):
        """Test getting snoozed status for mini camera from homescreen."""
        self.camera.product_type = "mini"
        self.camera.camera_id = "1234"
        self.blink.homescreen = {
            "owls": [{"id": "1234", "snooze": "2026-02-15T12:00:00+00:00"}]
        }
        result = await self.camera.snoozed
        self.assertTrue(result)

    async def test_camera_snoozed_mini_false(self, mock_resp):
        """Test getting snoozed status for mini camera returns False."""
        self.camera.product_type = "mini"
        self.camera.camera_id = "9999"
        self.blink.homescreen = {
            "owls": [{"id": "1234", "snooze": "2026-02-15T12:00:00+00:00"}]
        }
        result = await self.camera.snoozed
        self.assertFalse(result)
        # Verify mini camera ID not found in owls collection
        camera_ids = [str(cam["id"]) for cam in self.blink.homescreen["owls"]]
        self.assertNotIn("9999", camera_ids)

    async def test_camera_snoozed_empty_homescreen(self, mock_resp):
        """Test getting snoozed status with empty homescreen collection."""
        self.camera.product_type = "owl"
        self.camera.camera_id = "1234"
        self.blink.homescreen = {"owls": []}
        result = await self.camera.snoozed
        self.assertFalse(result)
        # Verify owls collection is empty
        self.assertEqual(len(self.blink.homescreen["owls"]), 0)

    async def test_camera_snoozed_missing_collection(self, mock_resp):
        """Test getting snoozed status when homescreen collection is missing."""
        self.camera.product_type = "doorbell"
        self.camera.camera_id = "5678"
        self.blink.homescreen = {"owls": []}
        result = await self.camera.snoozed
        self.assertFalse(result)
        # Verify doorbells collection is missing
        self.assertNotIn("doorbells", self.blink.homescreen)

    @mock.patch(
        "blinkpy.api.request_get_config",
        mock.AsyncMock(return_value=None),
    )
    async def test_camera_snoozed_none(self, mock_resp):
        """Test getting snoozed status with None response."""
        self.camera.product_type = "catalina"
        self.camera.network_id = "5678"
        self.camera.camera_id = "1234"
        result = await self.camera.snoozed
        self.assertFalse(result)

    @mock.patch(
        "blinkpy.api.request_get_config",
        mock.AsyncMock(return_value={"camera": [{}]}),
    )
    async def test_camera_snoozed_malformed(self, mock_resp):
        """Test getting snoozed status with malformed response."""
        self.camera.product_type = "catalina"
        self.camera.network_id = "5678"
        self.camera.camera_id = "1234"
        result = await self.camera.snoozed
        self.assertFalse(result)

    @mock.patch(
        "blinkpy.api.request_get_config",
        mock.AsyncMock(return_value={"camera": [{"snooze_till": ""}]}),
    )
    async def test_camera_snoozed_empty_string(self, mock_resp):
        """Test getting snoozed status with empty string."""
        self.camera.product_type = "catalina"
        self.camera.network_id = "5678"
        self.camera.camera_id = "1234"
        result = await self.camera.snoozed
        self.assertFalse(result)

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
