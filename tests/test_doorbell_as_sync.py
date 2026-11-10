"""Tests camera and system functions."""

from unittest import mock
from unittest import IsolatedAsyncioTestCase
import pytest
from blinkpy.blinkpy import Blink
from blinkpy.helpers.util import BlinkURLHandler
from blinkpy.sync_module import BlinkLotus
from blinkpy.camera import BlinkDoorbell


@mock.patch("blinkpy.auth.Auth.query")
class TestBlinkDoorbell(IsolatedAsyncioTestCase):
    """Test BlinkDoorbell functions in blinkpy."""

    def setUp(self):
        """Set up Blink module."""
        self.blink = Blink(motion_interval=0, session=mock.AsyncMock())
        self.blink.last_refresh = 0
        self.blink.urls = BlinkURLHandler("test")
        response = {
            "name": "test",
            "id": 3,
            "serial": "test123",
            "enabled": True,
            "network_id": 1,
            "thumbnail": "/foo/bar",
        }
        self.blink.homescreen = {"doorbells": [response]}
        self.blink.sync["test"] = BlinkLotus(self.blink, "test", "1234", response)
        self.blink.sync["test"].network_info = {"network": {"armed": True}}

    def tearDown(self):
        """Clean up after test."""
        self.blink = None

    def test_sync_attributes(self, mock_resp):
        """Test sync attributes."""
        self.assertEqual(self.blink.sync["test"].attributes["name"], "test")
        self.assertEqual(self.blink.sync["test"].attributes["network_id"], "1234")

    @pytest.mark.asyncio
    async def test_lotus_start(self, mock_resp):
        """Test doorbell instantiation."""
        self.blink.last_refresh = None
        lotus = self.blink.sync["test"]
        self.assertTrue(await lotus.start())
        self.assertTrue("test" in lotus.cameras)
        self.assertEqual(lotus.cameras["test"].__class__, BlinkDoorbell)

    @pytest.mark.asyncio
    async def test_doorbell_sensor_info(self, mock_resp):
        """Test doorbell sensors come from the doorbell config endpoint."""
        self.blink.auth.account_id = 7
        doorbell = BlinkDoorbell(self.blink.sync["test"])
        doorbell.network_id = "1234"
        doorbell.camera_id = "3"
        mock_resp.return_value = {
            "temp": 72,
            "wifi_rssi": -60,
            "last_connect": {"battery_voltage": 115},
        }
        await doorbell.get_sensor_info()
        self.assertEqual(
            mock_resp.call_args.kwargs["url"],
            "https://rest-test.immedia-semi.com/api/v1/accounts/7"
            "/networks/1234/doorbells/3/config",
        )
        self.assertEqual(doorbell.wifi_strength, -60)
        self.assertEqual(doorbell.temperature_calibrated, 72)
        self.assertEqual(doorbell.temperature_c, 22.2)
        self.assertEqual(doorbell.battery_voltage, 115)

        for failed in (None, {"message": "Unauthorized"}):
            mock_resp.return_value = failed
            with self.assertLogs("blinkpy.camera", level="WARNING"):
                await doorbell.get_sensor_info()
            self.assertEqual(doorbell.wifi_strength, -60)
            self.assertEqual(doorbell.temperature_calibrated, 72)
