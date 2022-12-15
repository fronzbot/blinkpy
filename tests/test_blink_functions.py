"""Tests camera and system functions."""
import unittest
from unittest import mock
import time
import random

from blinkpy import blinkpy
from blinkpy.sync_module import BlinkSyncModule
from blinkpy.camera import BlinkCamera
from blinkpy.helpers.util import get_time, BlinkURLHandler


class MockSyncModule(BlinkSyncModule):
    """Mock blink sync module object."""

    def get_network_info(self):
        """Mock network info method."""
        return True


class MockCamera(BlinkCamera):
    """Mock blink camera object."""

    def __init__(self, sync):
        """Initialize mock camera."""
        super().__init__(sync)
        self.camera_id = random.randint(1, 100000)

    def update(self, config, force_cache=False, **kwargs):
        """Mock camera update method."""


class TestBlinkFunctions(unittest.TestCase):
    """Test Blink and BlinkCamera functions in blinkpy."""

    def setUp(self):
        """Set up Blink module."""
        self.blink = blinkpy.Blink()
        self.blink.urls = BlinkURLHandler("test")

    def tearDown(self):
        """Clean up after test."""
        self.blink = None

    def test_merge_cameras(self):
        """Test merge camera functionality."""
        first_dict = {"foo": "bar", "test": 123}
        next_dict = {"foobar": 456, "bar": "foo"}
        self.blink.sync["foo"] = BlinkSyncModule(self.blink, "foo", 1, [])
        self.blink.sync["bar"] = BlinkSyncModule(self.blink, "bar", 2, [])
        self.blink.sync["foo"].cameras = first_dict
        self.blink.sync["bar"].cameras = next_dict
        result = self.blink.merge_cameras()
        expected = {"foo": "bar", "test": 123, "foobar": 456, "bar": "foo"}
        self.assertEqual(expected, result)

    @mock.patch("blinkpy.blinkpy.api.request_videos")
    def test_download_video_exit(self, mock_req):
        """Test we exit method when provided bad response."""
        blink = blinkpy.Blink()
        blink.last_refresh = 0
        mock_req.return_value = {}
        formatted_date = get_time(blink.last_refresh)
        expected_log = [
            "INFO:blinkpy.blinkpy:Retrieving videos since {}".format(formatted_date),
            "DEBUG:blinkpy.blinkpy:Processing page 1",
            "INFO:blinkpy.blinkpy:No videos found on page 1. Exiting.",
        ]
        with self.assertLogs(level="DEBUG") as dl_log:
            blink.download_videos("/tmp")
        self.assertListEqual(dl_log.output, expected_log)

    @mock.patch("blinkpy.blinkpy.api.request_videos")
    def test_parse_downloaded_items(self, mock_req):
        """Test ability to parse downloaded items list."""
        blink = blinkpy.Blink()
        generic_entry = {
            "created_at": "1970",
            "device_name": "foo",
            "deleted": True,
            "media": "/bar.mp4",
        }
        result = [generic_entry]
        mock_req.return_value = {"media": result}
        blink.last_refresh = 0
        formatted_date = get_time(blink.last_refresh)
        expected_log = [
            "INFO:blinkpy.blinkpy:Retrieving videos since {}".format(formatted_date),
            "DEBUG:blinkpy.blinkpy:Processing page 1",
            "DEBUG:blinkpy.blinkpy:foo: /bar.mp4 is marked as deleted.",
        ]
        with self.assertLogs(level="DEBUG") as dl_log:
            blink.download_videos("/tmp", stop=2, delay=0)
        self.assertListEqual(dl_log.output, expected_log)

    @mock.patch("blinkpy.blinkpy.api.request_videos")
    def test_parse_downloaded_throttle(self, mock_req):
        """Test ability to parse downloaded items list."""
        generic_entry = {
            "created_at": "1970",
            "device_name": "foo",
            "deleted": False,
            "media": "/bar.mp4",
        }
        result = [generic_entry]
        mock_req.return_value = {"media": result}
        self.blink.last_refresh = 0
        start = time.time()
        self.blink.download_videos("/tmp", stop=2, delay=0, debug=True)
        now = time.time()
        delta = now - start
        self.assertTrue(delta < 0.1)

        start = time.time()
        self.blink.download_videos("/tmp", stop=2, delay=0.1, debug=True)
        now = time.time()
        delta = now - start
        self.assertTrue(delta >= 0.1)

    @mock.patch("blinkpy.blinkpy.api.request_videos")
    def test_parse_camera_not_in_list(self, mock_req):
        """Test ability to parse downloaded items list."""
        blink = blinkpy.Blink()
        generic_entry = {
            "created_at": "1970",
            "device_name": "foo",
            "deleted": True,
            "media": "/bar.mp4",
        }
        result = [generic_entry]
        mock_req.return_value = {"media": result}
        blink.last_refresh = 0
        formatted_date = get_time(blink.last_refresh)
        expected_log = [
            "INFO:blinkpy.blinkpy:Retrieving videos since {}".format(formatted_date),
            "DEBUG:blinkpy.blinkpy:Processing page 1",
            "DEBUG:blinkpy.blinkpy:Skipping videos for foo.",
        ]
        with self.assertLogs(level="DEBUG") as dl_log:
            blink.download_videos("/tmp", camera="bar", stop=2, delay=0)
        self.assertListEqual(dl_log.output, expected_log)

    @mock.patch("blinkpy.blinkpy.api.request_network_update")
    @mock.patch("blinkpy.auth.Auth.query")
    def test_refresh(self, mock_req, mock_update):
        """Test ability to refresh system."""
        mock_update.return_value = {"network": {"sync_module_error": False}}
        mock_req.return_value = None
        self.blink.last_refresh = 0
        self.blink.available = True
        self.blink.sync["foo"] = MockSyncModule(self.blink, "foo", 1, [])
        self.blink.cameras = {"bar": MockCamera(self.blink.sync)}
        self.blink.sync["foo"].cameras = self.blink.cameras
        self.assertTrue(self.blink.refresh())
