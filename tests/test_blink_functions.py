"""Tests camera and system functions."""
import unittest
from unittest import mock

import pytest

from blinkpy import blinkpy
from blinkpy.sync_module import BlinkSyncModule
from blinkpy.camera import BlinkCamera
from blinkpy.helpers.constants import BLINK_URL
import tests.mock_responses as mresp

USERNAME = 'foobar'
PASSWORD = 'deadbeef'


class TestBlinkFunctions(unittest.TestCase):
    """Test Blink and BlinkCamera functions in blinkpy."""

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
        self.blink.sync = BlinkSyncModule(
            self.blink, self.blink._auth_header, self.blink.urls)

        self.camera = BlinkCamera(self.config, self.blink.sync)

    def tearDown(self):
        """Clean up after test."""
        self.blink = None
        self.config = {}
        self.camera = None

    @mock.patch('blinkpy.sync_module.http_req')
    def test_get_videos(self, req):
        """Test video access."""
        req.return_value = [
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

    @mock.patch('blinkpy.sync_module.BlinkSyncModule.refresh')
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

    @pytest.mark.skip(reason="Need to mock sync class.")
    @mock.patch('blinkpy.camera.http_req')
    def test_image_refresh(self, req):
        """Test image refresh function."""
        req.return_value = {'devices': [self.config]}
        image = self.camera.image_refresh()
        self.assertEqual(image,
                         'https://rest.test.{}/test.jpg'.format(BLINK_URL))

    @mock.patch('blinkpy.sync_module.http_req')
    def test_video_count(self, req):
        """Test video count function."""
        req.return_value = {'count': 1}
        self.assertEqual(self.blink.sync.video_count, 1)

    @pytest.mark.skip(reason="Need to mock Blink class, not methods")
    @mock.patch('blinkpy.sync_module.http_req')
    @mock.patch('blinkpy.sync_module.BlinkSyncModule._video_request')
    def test_refresh(self, vid_req, req):
        """Test blinkpy refresh function."""
        self.blink.sync.cameras = {'foobar': self.camera}
        req.return_value = {'devices': [self.config]}
        vid_req.return_value = [
            {
                'camera_name': 'foobar',
                'address': '/new.mp4',
                'thumbnail': '/new'
            }
        ]
        self.blink.last_refresh = -1
        self.blink.sync.refresh()
        test_camera = self.blink.sync.cameras['foobar']
        self.assertEqual(test_camera.clip,
                         'https://rest.test.{}/new.mp4'.format(BLINK_URL))
        self.assertEqual(test_camera.thumbnail,
                         'https://rest.test.{}/new.jpg'.format(BLINK_URL))

    def test_set_links(self):
        """Test the link set method."""
        self.blink.sync.cameras = {'foobar': self.camera}
        self.blink.network_id = 9999
        self.blink.sync.set_links()
        net_url = "{}/{}".format(self.blink.urls.network_url, 9999)
        self.assertEqual(self.camera.image_link,
                         "{}/camera/1111/thumbnail".format(net_url))
        self.assertEqual(self.camera.arm_link,
                         "{}/camera/1111/".format(net_url))

    @mock.patch('blinkpy.blinkpy.http_req')
    def test_backup_url(self, req):
        """Test backup login method."""
        req.side_effect = [
            mresp.mocked_requests_post(None),
            {'authtoken': {'authtoken': 'foobar123'}}
        ]
        self.blink.get_auth_token()
        self.assertEqual(self.blink.region_id, 'piri')
        self.assertEqual(self.blink.region, 'UNKNOWN')
