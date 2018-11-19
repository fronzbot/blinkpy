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
        self.blink.sync = BlinkSyncModule(self.blink)
        self.camera = BlinkCamera(self.blink.sync)

    def tearDown(self):
        """Clean up after test."""
        self.blink = None
        self.camera = None

    def test_get_events(self, mock_resp):
        """Test get events function."""
        mock_resp.return_value = {'event': True}
        self.assertEqual(self.blink.sync.get_events(), True)

    def test_get_camera_info(self, mock_resp):
        """Test get camera info function."""
        mock_resp.return_value = {'devicestatus': True}
        self.assertEqual(self.blink.sync.get_camera_info(), True)

    def test_get_videos_one_page(self, mock_resp):
        """Test video access."""
        mock_resp.return_value = [
            {
                'camera_name': 'foobar',
                'address': '/test/clip_1900_01_01_12_00_00AM.mp4',
                'thumbnail': '/test/thumb'
            }
        ]
        expected_videos = {'foobar': [
            {'clip': '/test/clip_1900_01_01_12_00_00AM.mp4',
             'thumb': '/test/thumb'}]}
        expected_records = {'foobar': ['1900_01_01_12_00_00AM']}
        expected_clips = {'foobar': {
            '1900_01_01_12_00_00AM': '/test/clip_1900_01_01_12_00_00AM.mp4'}}
        self.blink.sync.get_videos(start_page=0, end_page=0)
        self.assertEqual(self.blink.sync.videos, expected_videos)
        self.assertEqual(self.blink.sync.record_dates, expected_records)
        self.assertEqual(self.blink.sync.all_clips, expected_clips)

    def test_get_videos_multi_page(self, mock_resp):
        """Test video access with multiple pages."""
        mock_resp.return_value = [
            {
                'camera_name': 'test',
                'address': '/foo/bar_1900_01_01_12_00_00AM.mp4',
                'thumbnail': '/foobar'
            }
        ]
        self.blink.sync.get_videos()
        self.assertEqual(mock_resp.call_count, 2)
        mock_resp.reset_mock()
        self.blink.sync.get_videos(start_page=0, end_page=9)
        self.assertEqual(mock_resp.call_count, 10)

    def test_sync_start(self, mock_resp):
        """Test sync start function."""
        mock_resp.side_effect = [
            {'syncmodule': {
                'name': 'test',
                'id': 1234,
                'network_id': 5678,
                'serial': '12345678',
                'status': 'foobar'}},
            {'event': True},
            {},
            {},
            {'devicestatus': {}},
            None,
            None
        ]
        self.blink.sync.start()
        self.assertEqual(self.blink.sync.name, 'test')
        self.assertEqual(self.blink.sync.sync_id, 1234)
        self.assertEqual(self.blink.sync.network_id, 5678)
        self.assertEqual(self.blink.sync.serial, '12345678')
        self.assertEqual(self.blink.sync.status, 'foobar')
