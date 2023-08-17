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
