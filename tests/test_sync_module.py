"""Tests camera and system functions."""
import unittest
from unittest import mock

from blinkpy import blinkpy
from blinkpy.sync_module import BlinkSyncModule
from blinkpy.camera import BlinkCamera

USERNAME = 'foobar'
PASSWORD = 'deadbeef'


class MockSyncModule(BlinkSyncModule):
    """Mock http requests from sync module."""

    def __init__(self, blink, header):
        """Create mock sync module instance."""
        super().__init__(blink, header)
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
        self.config = {
            'device_id': 1111,
            'name': 'foobar',
            'armed': False,
            'active': 'disabled',
            'thumbnail': '/test',
            'video': '/test.mp4',
            'temp': 80,
            'battery': 3,
            'notifications': 2,
            'region_id': 'test',
            'device_type': 'camera'
        }
        self.blink.sync = MockSyncModule(
            self.blink, self.blink._auth_header)

        self.camera = BlinkCamera(self.config, self.blink.sync)

    def tearDown(self):
        """Clean up after test."""
        self.blink = None
        self.config = {}
        self.camera = None

    def test_get_videos(self):
        """Test video access."""
        self.blink.sync.return_value = [
            {
                'camera_name': 'foobar',
                'address': '/new/test.mp4',
                'thumbnail': '/test/thumb'
            }
        ]
        self.blink.sync.get_videos()
        self.assertEqual(self.blink.sync.videos['foobar'][0]['clip'],
                         '/new/test.mp4')
        self.assertEqual(self.blink.sync.videos['foobar'][0]['thumb'],
                         '/test/thumb')

    @mock.patch('blinkpy.blinkpy.Blink.refresh')
    @mock.patch('blinkpy.sync_module.BlinkSyncModule._summary_request')
    @mock.patch('blinkpy.sync_module.BlinkSyncModule._video_request')
    def test_get_cameras(self, vid_req, req, refresh):
        """Test camera extraction."""
        refresh.return_value = True
        req.return_value = {'devices': [self.config]}
        vid_req.return_value = [
            {
                'camera_name': 'foobar',
                'address': '/new.mp4',
                'thumbnail': '/new'
            }
        ]
        self.blink.sync.get_cameras()
        self.assertTrue('foobar' in self.blink.sync.cameras)

    def test_video_count(self):
        """Test video count function."""
        self.blink.sync.return_value = {'count': 1}
        self.assertEqual(self.blink.sync.video_count, 1)
