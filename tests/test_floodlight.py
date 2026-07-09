"""Tests for wired floodlight (superior) camera support."""

from unittest import mock
from unittest import IsolatedAsyncioTestCase
from blinkpy import api
from blinkpy.auth import Auth
from blinkpy.blinkpy import Blink, util
from blinkpy.sync_module import BlinkSyncModule
from blinkpy.camera import BlinkCamera

ACCOUNT_ID = 1111
NETWORK_ID = "2222"
CAMERA_ID = "3333"

COMMAND_RESPONSE = {"network_id": NETWORK_ID, "id": "9999", "state": "done"}
BUSY_RESPONSE = {"message": "System is busy, please wait", "error": None, "code": 307}


@mock.patch("blinkpy.auth.Auth.query")
class TestRequestFloodlight(IsolatedAsyncioTestCase):
    """Test api.request_floodlight."""

    async def asyncSetUp(self):
        """Set up Blink module."""
        self.blink = Blink(session=mock.AsyncMock())
        self.blink.urls = util.BlinkURLHandler("region_id")
        self.blink.auth = Auth(session=mock.AsyncMock())
        self.blink.auth.account_id = ACCOUNT_ID

    def tearDown(self):
        """Clean up after test."""
        self.blink = None

    async def test_request_floodlight_on(self, mock_resp):
        """Test request_floodlight posts to the correct URL for on."""
        mock_resp.return_value = COMMAND_RESPONSE
        result = await api.request_floodlight(self.blink, NETWORK_ID, CAMERA_ID, True)
        self.assertEqual(result, COMMAND_RESPONSE)
        call_url = mock_resp.call_args[1]["url"]
        self.assertIn(f"/owls/{CAMERA_ID}/lights/on", call_url)

    async def test_request_floodlight_off(self, mock_resp):
        """Test request_floodlight posts to the correct URL for off."""
        mock_resp.return_value = COMMAND_RESPONSE
        result = await api.request_floodlight(self.blink, NETWORK_ID, CAMERA_ID, False)
        self.assertEqual(result, COMMAND_RESPONSE)
        call_url = mock_resp.call_args[1]["url"]
        self.assertIn(f"/owls/{CAMERA_ID}/lights/off", call_url)

    async def test_request_floodlight_failure(self, mock_resp):
        """Test request_floodlight returns None on failure."""
        mock_resp.return_value = None
        result = await api.request_floodlight(self.blink, NETWORK_ID, CAMERA_ID, True)
        self.assertIsNone(result)


@mock.patch("blinkpy.auth.Auth.query", return_value={})
class TestFloodlightCamera(IsolatedAsyncioTestCase):
    """Test BlinkCamera floodlight methods."""

    def setUp(self):
        """Set up Blink module with a superior camera."""
        self.blink = Blink(session=mock.AsyncMock())
        self.blink.urls = util.BlinkURLHandler("test")
        self.blink.auth = Auth(session=mock.AsyncMock())
        self.blink.auth.account_id = ACCOUNT_ID
        self.blink.sync["test"] = BlinkSyncModule(self.blink, "test", NETWORK_ID, [])
        self.camera = BlinkCamera(self.blink.sync["test"])
        self.camera.name = "test_camera"
        self.camera.camera_id = CAMERA_ID
        self.camera.network_id = NETWORK_ID
        self.camera.product_type = "superior"
        self.blink.sync["test"].cameras["test_camera"] = self.camera

    def tearDown(self):
        """Clean up after test."""
        self.blink = None
        self.camera = None

    def test_floodlight_enabled_default(self, mock_resp):
        """Test floodlight_enabled returns None when not yet set."""
        self.assertIsNone(self.camera.floodlight_enabled)

    @mock.patch(
        "blinkpy.api.request_floodlight",
        mock.AsyncMock(return_value=COMMAND_RESPONSE),
    )
    async def test_async_set_floodlight_on(self, mock_resp):
        """Test async_set_floodlight turns light on and caches state."""
        result = await self.camera.async_set_floodlight(True)
        self.assertEqual(result, COMMAND_RESPONSE)
        self.assertTrue(self.camera.floodlight_enabled)

    @mock.patch(
        "blinkpy.api.request_floodlight",
        mock.AsyncMock(return_value=COMMAND_RESPONSE),
    )
    async def test_async_set_floodlight_off(self, mock_resp):
        """Test async_set_floodlight turns light off and caches state."""
        result = await self.camera.async_set_floodlight(False)
        self.assertEqual(result, COMMAND_RESPONSE)
        self.assertFalse(self.camera.floodlight_enabled)

    @mock.patch(
        "blinkpy.api.request_floodlight",
        mock.AsyncMock(return_value=None),
    )
    async def test_async_set_floodlight_api_failure(self, mock_resp):
        """Test async_set_floodlight returns None and does not cache on API failure."""
        result = await self.camera.async_set_floodlight(True)
        self.assertIsNone(result)
        self.assertIsNone(self.camera.floodlight_enabled)

    @mock.patch(
        "blinkpy.api.request_floodlight",
        mock.AsyncMock(return_value=BUSY_RESPONSE),
    )
    async def test_async_set_floodlight_busy(self, mock_resp):
        """Test async_set_floodlight returns None and does not cache when busy."""
        result = await self.camera.async_set_floodlight(True)
        self.assertIsNone(result)
        self.assertIsNone(self.camera.floodlight_enabled)

    @mock.patch(
        "blinkpy.api.request_floodlight",
        mock.AsyncMock(return_value=COMMAND_RESPONSE),
    )
    async def test_async_set_floodlight_non_superior_warns(self, mock_resp):
        """Test async_set_floodlight logs a warning for non-superior cameras."""
        self.camera.product_type = "hawk"
        with self.assertLogs("blinkpy.camera", level="WARNING") as log:
            await self.camera.async_set_floodlight(True)
        self.assertTrue(any("not a wired floodlight" in line for line in log.output))
