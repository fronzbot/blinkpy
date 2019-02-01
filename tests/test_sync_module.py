"""Tests camera and system functions."""
import unittest
from unittest import mock

from blinkpy import blinkpy
from blinkpy.sync_module import BlinkSyncModule
from blinkpy.camera import BlinkCamera

USERNAME = 'foobar'
PASSWORD = 'deadbeef'


@mock.patch('blinkpy.api.http_req')
class TestBlinkSyncModule(unittest.TestCase):
    """Test BlinkSyncModule functions in blinkpy."""

    def setUp(self):
        """Set up Blink module."""
        self.blink = blinkpy.Blink(username=USERNAME,
                                   password=PASSWORD)
        # pylint: disable=protected-access
        self.blink._auth_header = {
            'Host': 'test.url.tld',
            'TOKEN_AUTH': 'foobar123'
        }
        self.blink.urls = blinkpy.BlinkURLHandler('test')
        self.blink.sync['test'] = BlinkSyncModule(self.blink, 'test', '1234')
        self.camera = BlinkCamera(self.blink.sync)
        self.mock_start = [
            {'syncmodule': {
                'id': 1234,
                'network_id': 5678,
                'serial': '12345678',
                'status': 'foobar'}},
            {'event': True},
            {},
            {},
            None,
            {'devicestatus': {}},
        ]

    def tearDown(self):
        """Clean up after test."""
        self.blink = None
        self.camera = None
        self.mock_start = None

    def test_get_events(self, mock_resp):
        """Test get events function."""
        mock_resp.return_value = {'event': True}
        self.assertEqual(self.blink.sync['test'].get_events(), True)

    def test_get_camera_info(self, mock_resp):
        """Test get camera info function."""
        mock_resp.return_value = {'devicestatus': True}
        self.assertEqual(self.blink.sync['test'].get_camera_info(), True)

    def test_check_new_videos(self, mock_resp):
        """Test recent video response."""
        mock_resp.return_value = {
            'videos': [{
                'camera_name': 'foo',
                'address': '/foo/bar.mp4',
                'created_at': '1970-01-01T00:00:00+0:00'
            }]
        }
        sync_module = self.blink.sync['test']
        sync_module.cameras = {'foo': None}
        self.assertEqual(sync_module.motion, {})
        self.assertTrue(sync_module.check_new_videos())
        self.assertEqual(sync_module.last_record['foo'],
                         {'clip': '/foo/bar.mp4',
                          'time': '1970-01-01T00:00:00+0:00'})
        self.assertEqual(sync_module.motion, {'foo': True})
        mock_resp.return_value = {'videos': []}
        self.assertTrue(sync_module.check_new_videos())
        self.assertEqual(sync_module.motion, {'foo': False})
        self.assertEqual(sync_module.last_record['foo'],
                         {'clip': '/foo/bar.mp4',
                          'time': '1970-01-01T00:00:00+0:00'})

    def test_check_new_videos_failed(self, mock_resp):
        """Test method when response is unexpected."""
        mock_resp.side_effect = [None, 'just a string', {}]
        sync_module = self.blink.sync['test']
        sync_module.cameras = {'foo': None}

        sync_module.motion['foo'] = True
        self.assertFalse(sync_module.check_new_videos())
        self.assertFalse(sync_module.motion['foo'])

        sync_module.motion['foo'] = True
        self.assertFalse(sync_module.check_new_videos())
        self.assertFalse(sync_module.motion['foo'])

        sync_module.motion['foo'] = True
        self.assertFalse(sync_module.check_new_videos())
        self.assertFalse(sync_module.motion['foo'])

    def test_sync_start(self, mock_resp):
        """Test sync start function."""
        mock_resp.side_effect = self.mock_start
        self.blink.sync['test'].start()
        self.assertEqual(self.blink.sync['test'].name, 'test')
        self.assertEqual(self.blink.sync['test'].sync_id, 1234)
        self.assertEqual(self.blink.sync['test'].network_id, 5678)
        self.assertEqual(self.blink.sync['test'].serial, '12345678')
        self.assertEqual(self.blink.sync['test'].status, 'foobar')

    def test_unexpected_summary(self, mock_resp):
        """Test unexpected summary response."""
        self.mock_start[0] = None
        mock_resp.side_effect = self.mock_start
        self.assertFalse(self.blink.sync['test'].start())

    def test_summary_with_no_network_id(self, mock_resp):
        """Test handling of bad summary."""
        self.mock_start[0]['syncmodule'] = None
        mock_resp.side_effect = self.mock_start
        self.assertFalse(self.blink.sync['test'].start())

    def test_summary_with_only_network_id(self, mock_resp):
        """Test handling of sparse summary."""
        self.mock_start[0]['syncmodule'] = {'network_id': 8675309}
        mock_resp.side_effect = self.mock_start
        self.blink.sync['test'].start()
        self.assertEqual(self.blink.sync['test'].network_id, 8675309)

    def test_unexpected_events(self, mock_resp):
        """Test unexpected events response."""
        self.mock_start[1] = None
        mock_resp.side_effect = self.mock_start
        self.blink.sync['test'].start()
        self.assertEqual(self.blink.sync['test'].events, False)

    def test_missing_events(self, mock_resp):
        """Test missing events key from response."""
        self.mock_start[1] = {}
        mock_resp.side_effect = self.mock_start
        self.blink.sync['test'].start()
        self.assertEqual(self.blink.sync['test'].events, False)

    def test_unexpected_camera_info(self, mock_resp):
        """Test unexpected camera info response."""
        self.blink.sync['test'].cameras['foo'] = None
        self.mock_start[5] = None
        mock_resp.side_effect = self.mock_start
        self.blink.sync['test'].start()
        self.assertEqual(self.blink.sync['test'].cameras, {'foo': None})

    def test_missing_camera_info(self, mock_resp):
        """Test missing key from camera info response."""
        self.blink.sync['test'].cameras['foo'] = None
        self.mock_start[5] = {}
        self.blink.sync['test'].start()
        self.assertEqual(self.blink.sync['test'].cameras, {'foo': None})
