"""Tests camera and system functions."""

import json
import unittest
from unittest import mock

from random import shuffle

from blinkpy.blinkpy import Blink
from blinkpy.helpers.util import BlinkURLHandler
from blinkpy.sync_module import BlinkSyncModule
from blinkpy.camera import BlinkCamera, BlinkCameraMini, BlinkDoorbell


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
            sync_module.last_records["foo"],
            [{"clip": "/foo/bar.mp4", "time": "1990-01-01T00:00:00+00:00"}],
        )
        self.assertEqual(sync_module.motion, {"foo": True})
        mock_resp.return_value = {"media": []}
        self.assertTrue(sync_module.check_new_videos())
        self.assertEqual(sync_module.motion, {"foo": False})
        self.assertEqual(
            sync_module.last_records["foo"],
            [{"clip": "/foo/bar.mp4", "time": "1990-01-01T00:00:00+00:00"}],
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
            "foo": [{"clip": "/bar/foo.mp4", "time": "1990-01-01T00:00:00+00:00"}]
        }
        self.assertEqual(sync_module.last_records, expected_result)

    def test_sync_start(self, mock_resp):
        """Test sync start function."""
        mock_resp.side_effect = self.mock_start
        self.blink.sync["test"].start()
        self.assertEqual(self.blink.sync["test"].name, "test")
        self.assertEqual(self.blink.sync["test"].sync_id, 1234)
        self.assertEqual(self.blink.sync["test"].network_id, 5678)
        self.assertEqual(self.blink.sync["test"].serial, "12345678")
        self.assertEqual(self.blink.sync["test"].status, "foobar")

    def test_sync_with_mixed_cameras(self, mock_resp):
        """Test sync module with mixed cameras attached."""
        resp_sync = {
            "syncmodule": {
                "network_id": 1234,
                "id": 1,
                "serial": 456,
                "status": "onboarded",
            }
        }
        resp_network_info = {"network": {"sync_module_error": False}}
        resp_videos = {"media": []}
        resp_empty = {}

        self.blink.sync["test"].camera_list = [
            {"name": "foo", "id": 10, "type": "default"},
            {"name": "bar", "id": 11, "type": "mini"},
            {"name": "fake", "id": 12, "type": "doorbell"},
        ]

        self.blink.homescreen = {
            "owls": [{"name": "bar", "id": 3}],
            "doorbells": [{"name": "fake", "id": 12}],
        }

        side_effect = [
            resp_sync,
            resp_network_info,
            resp_videos,
            resp_empty,
            resp_empty,
            resp_empty,
            resp_empty,
            resp_empty,
            resp_empty,
        ]

        mock_resp.side_effect = side_effect

        test_sync = self.blink.sync["test"]

        self.assertTrue(test_sync.start())
        self.assertEqual(test_sync.cameras["foo"].__class__, BlinkCamera)
        self.assertEqual(test_sync.cameras["bar"].__class__, BlinkCameraMini)
        self.assertEqual(test_sync.cameras["fake"].__class__, BlinkDoorbell)

        # Now shuffle the cameras and see if it still works
        for i in range(0, 10):
            shuffle(test_sync.camera_list)
            mock_resp.side_effect = side_effect
            self.assertTrue(test_sync.start())
            debug_msg = f"Iteration: {i}, {test_sync.camera_list}"
            self.assertEqual(
                test_sync.cameras["foo"].__class__, BlinkCamera, msg=debug_msg
            )
            self.assertEqual(
                test_sync.cameras["bar"].__class__, BlinkCameraMini, msg=debug_msg
            )
            self.assertEqual(
                test_sync.cameras["fake"].__class__, BlinkDoorbell, msg=debug_msg
            )

    def test_init_local_storage(self, mock_resp):
        """Test initialization of local storage object."""
        json_fragment = """{
            "sync_modules": [
                {
                    "id": 123456,
                    "name": "test",
                    "local_storage_enabled": true,
                    "local_storage_compatible": true,
                    "local_storage_status": "active"
                }
            ]
        }"""
        self.blink.homescreen = json.loads(json_fragment)
        self.blink.sync["test"]._init_local_storage(123456)
        self.assertTrue(self.blink.sync["test"].local_storage)
