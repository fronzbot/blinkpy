"""Tests camera and system functions."""

from unittest import mock
from unittest import IsolatedAsyncioTestCase
import pytest
from blinkpy.blinkpy import Blink
from blinkpy.helpers.util import BlinkURLHandler
from blinkpy.sync_module import BlinkOwl
from blinkpy.camera import BlinkCameraMini


@mock.patch("blinkpy.auth.Auth.query")
class TestBlinkSyncModule(IsolatedAsyncioTestCase):
    """Test BlinkSyncModule functions in blinkpy."""

    def setUp(self):
        """Set up Blink module."""
        self.blink = Blink(motion_interval=0, session=mock.AsyncMock())
        self.blink.last_refresh = 0
        self.blink.urls = BlinkURLHandler("test")
        response = {
            "name": "test",
            "id": 2,
            "serial": "foobar123",
            "enabled": True,
            "network_id": 1,
            "thumbnail": "/foo/bar",
        }
        self.blink.homescreen = {"owls": [response]}
        self.blink.sync["test"] = BlinkOwl(self.blink, "test", "1234", response)
        self.blink.sync["test"].network_info = {"network": {"armed": True}}

    def tearDown(self):
        """Clean up after test."""
        self.blink = None

    def test_sync_attributes(self, mock_resp):
        """Test sync attributes."""
        self.assertEqual(self.blink.sync["test"].attributes["name"], "test")
        self.assertEqual(self.blink.sync["test"].attributes["network_id"], "1234")

    @pytest.mark.asyncio
    async def test_owl_start(self, mock_resp):
        """Test owl camera instantiation."""
        self.blink.last_refresh = None
        owl = self.blink.sync["test"]
        self.assertTrue(await owl.start())
        self.assertTrue("test" in owl.cameras)
        self.assertEqual(owl.cameras["test"].__class__, BlinkCameraMini)

    def test_owl_arm_from_network(self, mock_resp):
        """Test that owl arm state reflects the network armed state."""
        owl = self.blink.sync["test"]
        # Network is disarmed even though camera enabled is True
        self.blink.homescreen["networks"] = [{"id": 1234, "armed": False}]
        self.assertFalse(owl.arm)
        self.assertFalse(owl.network_info["network"]["armed"])

        # Network is armed
        self.blink.homescreen["networks"] = [{"id": 1234, "armed": True}]
        self.assertTrue(owl.arm)
        self.assertTrue(owl.network_info["network"]["armed"])

    def test_owl_arm_fallback_to_status(self, mock_resp):
        """Test that owl arm state falls back to status if network not found."""
        owl = self.blink.sync["test"]
        self.blink.homescreen = {"owls": []}
        self.assertTrue(owl.arm)
