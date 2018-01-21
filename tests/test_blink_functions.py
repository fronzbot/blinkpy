"""Tests camera and system functions."""

import unittest
from unittest import mock
from blinkpy import blinkpy
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
            'thumbnail': '/test',
            'video': '/test.mp4',
            'temp': 80,
            'battery': 3,
            'notifications': 2,
            'region_id': 'test',
            'device_type': 'camera'
        }
        self.camera = blinkpy.BlinkCamera(self.config, self.blink)

    def tearDown(self):
        """Clean up after test."""
        self.blink = None
        self.config = {}
        self.camera = None

    @mock.patch('blinkpy.blinkpy._request')
    def test_get_videos(self, req):
        """Test video access."""
        req.return_value = [
            {
                'camera_name': 'foobar',
                'address': '/new/test.mp4',
                'thumbnail': '/test/thumb'
            }
        ]
        self.blink.get_videos()
        self.assertEqual(self.blink.videos['foobar'][0]['clip'],
                         '/new/test.mp4')
        self.assertEqual(self.blink.videos['foobar'][0]['thumb'],
                         '/test/thumb')

    @mock.patch('blinkpy.blinkpy._request')
    def test_get_cameras(self, req):
        """Test camera extraction."""
        req.return_value = {'devices': [self.config]}
        self.blink.get_cameras()
        self.assertTrue('foobar' in self.blink.cameras)

    @mock.patch('blinkpy.blinkpy._request')
    def test_image_refresh(self, req):
        """Test image refresh function."""
        req.return_value = {'devices': [self.config]}
        image = self.camera.image_refresh()
        self.assertEqual(image,
                         'https://rest.test.{}/test.jpg'.format(BLINK_URL))

    @mock.patch('blinkpy.blinkpy._request')
    def test_video_count(self, req):
        """Test video count function."""
        req.return_value = {'count': 1}
        self.assertEqual(self.blink.video_count, 1)

    @mock.patch('blinkpy.blinkpy._request')
    @mock.patch('blinkpy.blinkpy.Blink._video_request')
    def test_refresh(self, vid_req, req):
        """Test blinkpy refresh function."""
        self.blink.cameras = {'foobar': self.camera}
        req.return_value = {'devices': [self.config]}
        vid_req.return_value = [
            {
                'camera_name': 'foobar',
                'address': '/new.mp4',
                'thumbnail': '/new'
            }
        ]
        self.blink.refresh()
        test_camera = self.blink.cameras['foobar']
        self.assertEqual(test_camera.clip,
                         'https://rest.test.{}/new.mp4'.format(BLINK_URL))
        self.assertEqual(test_camera.thumbnail,
                         'https://rest.test.{}/new.jpg'.format(BLINK_URL))

    def test_set_links(self):
        """Test the link set method."""
        self.blink.cameras = {'foobar': self.camera}
        self.blink.network_id = 9999
        self.blink.set_links()
        net_url = "{}/{}".format(self.blink.urls.network_url, 9999)
        self.assertEqual(self.camera.image_link,
                         "{}/camera/1111/thumbnail".format(net_url))
        self.assertEqual(self.camera.arm_link,
                         "{}/camera/1111/".format(net_url))

    @mock.patch('blinkpy.blinkpy._request')
    def test_backup_url(self, req):
        """Test backup login method."""
        req.side_effect = [
            mresp.mocked_requests_post(None),
            {'authtoken': {'authtoken': 'foobar123'}}
        ]
        self.blink.get_auth_token()
        self.assertEqual(self.blink.region_id, 'piri')
        self.assertEqual(self.blink.region, 'UNKNOWN')
