"""Tests camera and system functions."""
import unittest
from unittest import mock

from blinkpy.blinkpy import Blink
from blinkpy.helpers.util import BlinkURLHandler
from blinkpy.sync_module import BlinkSyncModule, BlinkOwl
from blinkpy.camera import BlinkCamera, BlinkCameraMini


@mock.patch("blinkpy.auth.Auth.query")
class TestBlinkSyncModule(unittest.TestCase):
    """Test BlinkSyncModule functions in blinkpy."""

    def setUp(self):
        """Set up Blink module."""
        self.blink = Blink(motion_interval=0)
        self.blink.last_refresh = 0
        self.blink.urls = BlinkURLHandler("test")
        self.blink.sync["test"] = BlinkSyncModule(self.blink, "test", "1234", [])
        self.camera = BlinkCamera(self.blink.sync)
        self.mock_start = [
            {
                "syncmodule": {
                    "id": 1234,
                    "network_id": 5678,
                    "serial": "12345678",
                    "status": "foobar",
                }
            },
            {"event": True},
            {},
            {},
            None,
            {"devicestatus": {}},
        ]
        self.blink.sync["test"].network_info = {"network": {"armed": True}}

    def tearDown(self):
        """Clean up after test."""
        self.blink = None
        self.camera = None
        self.mock_start = None

    def test_bad_status(self, mock_resp):
        """Check that we mark module unavaiable on bad status."""
        self.blink.sync["test"].status = None
        self.blink.sync["test"].available = True
        self.assertFalse(self.blink.sync["test"].online)
        self.assertFalse(self.blink.sync["test"].available)

    def test_bad_arm(self, mock_resp):
        """Check that we mark module unavaiable if bad arm status."""
        self.blink.sync["test"].network_info = None
        self.blink.sync["test"].available = True
        self.assertEqual(self.blink.sync["test"].arm, None)
        self.assertFalse(self.blink.sync["test"].available)
        self.blink.sync["test"].network_info = {}
        self.blink.sync["test"].available = True
        self.assertEqual(self.blink.sync["test"].arm, None)
        self.assertFalse(self.blink.sync["test"].available)

    def test_get_events(self, mock_resp):
        """Test get events function."""
        mock_resp.return_value = {"event": True}
        self.assertEqual(self.blink.sync["test"].get_events(), True)

    def test_get_events_fail(self, mock_resp):
        """Test handling of failed get events function."""
        mock_resp.return_value = None
        self.assertFalse(self.blink.sync["test"].get_events())
        mock_resp.return_value = {}
        self.assertFalse(self.blink.sync["test"].get_events())

    def test_get_camera_info(self, mock_resp):
        """Test get camera info function."""
        mock_resp.return_value = {"camera": ["foobar"]}
        self.assertEqual(self.blink.sync["test"].get_camera_info("1234"), "foobar")

    def test_get_camera_info_fail(self, mock_resp):
        """Test handling of failed get camera info function."""
        mock_resp.return_value = None
        self.assertEqual(self.blink.sync["test"].get_camera_info("1"), {})
        mock_resp.return_value = {}
        self.assertEqual(self.blink.sync["test"].get_camera_info("1"), {})
        mock_resp.return_value = {"camera": None}
        self.assertEqual(self.blink.sync["test"].get_camera_info("1"), {})

    def test_get_network_info(self, mock_resp):
        """Test network retrieval."""
        mock_resp.return_value = {"network": {"sync_module_error": False}}
        self.assertTrue(self.blink.sync["test"].get_network_info())
        mock_resp.return_value = {"network": {"sync_module_error": True}}
        self.assertFalse(self.blink.sync["test"].get_network_info())

    def test_get_network_info_failure(self, mock_resp):
        """Test failed network retrieval."""
        mock_resp.return_value = {}
        self.blink.sync["test"].available = True
        self.assertFalse(self.blink.sync["test"].get_network_info())
        self.assertFalse(self.blink.sync["test"].available)
        self.blink.sync["test"].available = True
        mock_resp.return_value = None
        self.assertFalse(self.blink.sync["test"].get_network_info())
        self.assertFalse(self.blink.sync["test"].available)

    def test_check_new_videos_startup(self, mock_resp):
        """Test that check_new_videos does not block startup."""
        sync_module = self.blink.sync["test"]
        self.blink.last_refresh = None
        self.assertFalse(sync_module.check_new_videos())

    def test_check_new_videos(self, mock_resp):
        """Test recent video response."""
        mock_resp.return_value = {
            "media": [
                {
                    "device_name": "foo",
                    "media": "/foo/bar.mp4",
                    "created_at": "1990-01-01T00:00:00+00:00",
                }
            ]
        }

        sync_module = self.blink.sync["test"]
        sync_module.cameras = {"foo": None}
        sync_module.blink.last_refresh = 0
        self.assertEqual(sync_module.motion, {})
        self.assertTrue(sync_module.check_new_videos())
        self.assertEqual(
            sync_module.last_record["foo"],
            {"clip": "/foo/bar.mp4", "time": "1990-01-01T00:00:00+00:00"},
        )
        self.assertEqual(sync_module.motion, {"foo": True})
        mock_resp.return_value = {"media": []}
        self.assertTrue(sync_module.check_new_videos())
        self.assertEqual(sync_module.motion, {"foo": False})
        self.assertEqual(
            sync_module.last_record["foo"],
            {"clip": "/foo/bar.mp4", "time": "1990-01-01T00:00:00+00:00"},
        )

    def test_check_new_videos_old_date(self, mock_resp):
        """Test videos return response with old date."""
        mock_resp.return_value = {
            "media": [
                {
                    "device_name": "foo",
                    "media": "/foo/bar.mp4",
                    "created_at": "1970-01-01T00:00:00+00:00",
                }
            ]
        }

        sync_module = self.blink.sync["test"]
        sync_module.cameras = {"foo": None}
        sync_module.blink.last_refresh = 1000
        self.assertTrue(sync_module.check_new_videos())
        self.assertEqual(sync_module.motion, {"foo": False})

    def test_check_no_motion_if_not_armed(self, mock_resp):
        """Test that motion detection is not set if module unarmed."""
        mock_resp.return_value = {
            "media": [
                {
                    "device_name": "foo",
                    "media": "/foo/bar.mp4",
                    "created_at": "1990-01-01T00:00:00+00:00",
                }
            ]
        }
        sync_module = self.blink.sync["test"]
        sync_module.cameras = {"foo": None}
        sync_module.blink.last_refresh = 1000
        self.assertTrue(sync_module.check_new_videos())
        self.assertEqual(sync_module.motion, {"foo": True})
        sync_module.network_info = {"network": {"armed": False}}
        self.assertTrue(sync_module.check_new_videos())
        self.assertEqual(sync_module.motion, {"foo": False})

    def test_check_multiple_videos(self, mock_resp):
        """Test motion found even with multiple videos."""
        mock_resp.return_value = {
            "media": [
                {
                    "device_name": "foo",
                    "media": "/foo/bar.mp4",
                    "created_at": "1970-01-01T00:00:00+00:00",
                },
                {
                    "device_name": "foo",
                    "media": "/bar/foo.mp4",
                    "created_at": "1990-01-01T00:00:00+00:00",
                },
                {
                    "device_name": "foo",
                    "media": "/foobar.mp4",
                    "created_at": "1970-01-01T00:00:01+00:00",
                },
            ]
        }
        sync_module = self.blink.sync["test"]
        sync_module.cameras = {"foo": None}
        sync_module.blink.last_refresh = 1000
        self.assertTrue(sync_module.check_new_videos())
        self.assertEqual(sync_module.motion, {"foo": True})
        expected_result = {
            "foo": {"clip": "/bar/foo.mp4", "time": "1990-01-01T00:00:00+00:00"}
        }
        self.assertEqual(sync_module.last_record, expected_result)

    def test_check_new_videos_failed(self, mock_resp):
        """Test method when response is unexpected."""
        mock_resp.side_effect = [None, "just a string", {}]
        sync_module = self.blink.sync["test"]
        sync_module.cameras = {"foo": None}

        sync_module.motion["foo"] = True
        self.assertFalse(sync_module.check_new_videos())
        self.assertFalse(sync_module.motion["foo"])

        sync_module.motion["foo"] = True
        self.assertFalse(sync_module.check_new_videos())
        self.assertFalse(sync_module.motion["foo"])

        sync_module.motion["foo"] = True
        self.assertFalse(sync_module.check_new_videos())
        self.assertFalse(sync_module.motion["foo"])

    def test_sync_start(self, mock_resp):
        """Test sync start function."""
        mock_resp.side_effect = self.mock_start
        self.blink.sync["test"].start()
        self.assertEqual(self.blink.sync["test"].name, "test")
        self.assertEqual(self.blink.sync["test"].sync_id, 1234)
        self.assertEqual(self.blink.sync["test"].network_id, 5678)
        self.assertEqual(self.blink.sync["test"].serial, "12345678")
        self.assertEqual(self.blink.sync["test"].status, "foobar")

    def test_unexpected_summary(self, mock_resp):
        """Test unexpected summary response."""
        self.mock_start[0] = None
        mock_resp.side_effect = self.mock_start
        self.assertFalse(self.blink.sync["test"].start())

    def test_summary_with_no_network_id(self, mock_resp):
        """Test handling of bad summary."""
        self.mock_start[0]["syncmodule"] = None
        mock_resp.side_effect = self.mock_start
        self.assertFalse(self.blink.sync["test"].start())

    def test_summary_with_only_network_id(self, mock_resp):
        """Test handling of sparse summary."""
        self.mock_start[0]["syncmodule"] = {"network_id": 8675309}
        mock_resp.side_effect = self.mock_start
        self.blink.sync["test"].start()
        self.assertEqual(self.blink.sync["test"].network_id, 8675309)

    def test_unexpected_camera_info(self, mock_resp):
        """Test unexpected camera info response."""
        self.blink.sync["test"].cameras["foo"] = None
        self.mock_start[5] = None
        mock_resp.side_effect = self.mock_start
        self.blink.sync["test"].start()
        self.assertEqual(self.blink.sync["test"].cameras, {"foo": None})

    def test_missing_camera_info(self, mock_resp):
        """Test missing key from camera info response."""
        self.blink.sync["test"].cameras["foo"] = None
        self.mock_start[5] = {}
        self.blink.sync["test"].start()
        self.assertEqual(self.blink.sync["test"].cameras, {"foo": None})

    def test_sync_attributes(self, mock_resp):
        """Test sync attributes."""
        self.assertEqual(self.blink.sync["test"].attributes["name"], "test")
        self.assertEqual(self.blink.sync["test"].attributes["network_id"], "1234")

    def test_owl_start(self, mock_resp):
        """Test owl camera instantiation."""
        response = {
            "name": "foo",
            "id": 2,
            "serial": "foobar123",
            "enabled": True,
            "network_id": 1,
            "thumbnail": "/foo/bar",
        }
        self.blink.last_refresh = None
        self.blink.homescreen = {"owls": [response]}
        owl = BlinkOwl(self.blink, "foo", 1234, response)
        self.assertTrue(owl.start())
        self.assertTrue("foo" in owl.cameras)
        self.assertEqual(owl.cameras["foo"].__class__, BlinkCameraMini)
