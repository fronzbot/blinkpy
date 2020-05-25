"""Tests camera and system functions."""
import unittest
from unittest import mock
import logging

from blinkpy import blinkpy
from blinkpy.sync_module import BlinkSyncModule
from blinkpy.helpers.util import get_time, BlinkURLHandler


class MockSyncModule(BlinkSyncModule):
    """Mock http requests from sync module."""

    def __init__(self, blink, header):
        """Create mock sync module instance."""
        super().__init__(blink, header, network_id=None, camera_list=None)
        self.blink = blink
        self.header = header
        self.return_value = None
        self.return_value2 = None

    def http_get(self, url, stream=False, json=True):
        """Mock get request."""
        if stream and self.return_value2 is not None:
            return self.return_value2
        return self.return_value

    def http_post(self, url):
        """Mock post request."""
        return self.return_value


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
        # pylint: disable=protected-access
        blinkpy._LOGGER.setLevel(logging.DEBUG)
        blink.last_refresh = 0
        mock_req.return_value = {}
        formatted_date = get_time(blink.last_refresh)
        expected_log = [
            "INFO:blinkpy.blinkpy:Retrieving videos since {}".format(formatted_date),
            "DEBUG:blinkpy.blinkpy:Processing page 1",
            "INFO:blinkpy.blinkpy:No videos found on page 1. Exiting.",
        ]
        with self.assertLogs() as dl_log:
            blink.download_videos("/tmp")
        self.assertEqual(dl_log.output, expected_log)

    @mock.patch("blinkpy.blinkpy.api.request_videos")
    def test_parse_downloaded_items(self, mock_req):
        """Test ability to parse downloaded items list."""
        blink = blinkpy.Blink()
        # pylint: disable=protected-access
        blinkpy._LOGGER.setLevel(logging.DEBUG)
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
        with self.assertLogs() as dl_log:
            blink.download_videos("/tmp", stop=2)
        self.assertEqual(dl_log.output, expected_log)

    @mock.patch("blinkpy.blinkpy.api.request_videos")
    def test_parse_camera_not_in_list(self, mock_req):
        """Test ability to parse downloaded items list."""
        blink = blinkpy.Blink()
        # pylint: disable=protected-access
        blinkpy._LOGGER.setLevel(logging.DEBUG)
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
        with self.assertLogs() as dl_log:
            blink.download_videos("/tmp", camera="bar", stop=2)
        self.assertEqual(dl_log.output, expected_log)
