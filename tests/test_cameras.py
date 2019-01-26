"""
Test all camera attributes.

Tests the camera initialization and attributes of
individual BlinkCamera instantiations once the
Blink system is set up.
"""

import unittest
from unittest import mock
from blinkpy import blinkpy
from blinkpy.helpers.util import create_session, BlinkURLHandler
from blinkpy.sync_module import BlinkSyncModule
from blinkpy.camera import BlinkCamera
import tests.mock_responses as mresp

USERNAME = 'foobar'
PASSWORD = 'deadbeef'

CAMERA_CFG = {
    'camera': [
        {
            'battery_voltage': 90,
            'motion_alert': True,
            'wifi_strength': -30,
            'temperature': 68
        }
    ]
}


@mock.patch('blinkpy.helpers.util.Session.send',
            side_effect=mresp.mocked_session_send)
class TestBlinkCameraSetup(unittest.TestCase):
    """Test the Blink class in blinkpy."""

    def setUp(self):
        """Set up Blink module."""
        self.blink = blinkpy.Blink(username=USERNAME,
                                   password=PASSWORD)
        header = {
            'Host': 'abc.zxc',
            'TOKEN_AUTH': mresp.LOGIN_RESPONSE['authtoken']['authtoken']
        }
        # pylint: disable=protected-access
        self.blink._auth_header = header
        self.blink.session = create_session()
        self.blink.urls = BlinkURLHandler('test')
        self.blink.sync['test'] = BlinkSyncModule(self.blink, 'test', 1234)
        self.camera = BlinkCamera(self.blink.sync['test'])
        self.camera.name = 'foobar'
        self.blink.sync['test'].cameras['foobar'] = self.camera

    def tearDown(self):
        """Clean up after test."""
        self.blink = None

    def test_camera_update(self, mock_sess):
        """Test that we can properly update camera properties."""
        config = {
            'name': 'new',
            'camera_id': 1234,
            'network_id': 5678,
            'serial': '12345678',
            'enabled': False,
            'battery_voltage': 90,
            'battery_state': 'ok',
            'temperature': 68,
            'wifi_strength': 4,
            'thumbnail': '/thumb',
        }
        self.camera.last_record = ['1']
        self.camera.sync.last_record = {
            'new': {
                'clip': '/test.mp4',
                'time': '1970-01-01T00:00:00'
            }
        }
        mock_sess.side_effect = [
            mresp.MockResponse({'temp': 71}, 200),
            'test',
            'foobar'
        ]
        self.camera.update(config)
        self.assertEqual(self.camera.name, 'new')
        self.assertEqual(self.camera.camera_id, '1234')
        self.assertEqual(self.camera.network_id, '5678')
        self.assertEqual(self.camera.serial, '12345678')
        self.assertEqual(self.camera.motion_enabled, False)
        self.assertEqual(self.camera.battery, 50)
        self.assertEqual(self.camera.temperature, 68)
        self.assertEqual(self.camera.temperature_c, 20)
        self.assertEqual(self.camera.temperature_calibrated, 71)
        self.assertEqual(self.camera.wifi_strength, 4)
        self.assertEqual(self.camera.thumbnail,
                         'https://rest.test.immedia-semi.com/thumb.jpg')
        self.assertEqual(self.camera.clip,
                         'https://rest.test.immedia-semi.com/test.mp4')
        self.assertEqual(self.camera.image_from_cache, 'test')
        self.assertEqual(self.camera.video_from_cache, 'foobar')

    def test_thumbnail_not_in_info(self, mock_sess):
        """Test that we grab thumbanil if not in camera_info."""
        mock_sess.side_effect = [
            mresp.MockResponse({'temp': 71}, 200),
            'foobar',
            'barfoo'
        ]
        self.camera.last_record = ['1']
        self.camera.sync.last_record = {
            'new': {
                'clip': '/test.mp4',
                'time': '1970-01-01T00:00:00'
            }
        }
        config = {
            'name': 'new',
            'camera_id': 1234,
            'network_id': 5678,
            'serial': '12345678',
            'enabled': False,
            'battery_voltage': 90,
            'battery_state': 'ok',
            'temperature': 68,
            'wifi_strength': 4,
            'thumbnail': '',
        }
        self.camera.sync.homescreen = {
            'devices': [
                {'foo': 'bar'},
                {'device_type': 'foobar'},
                {'device_type': 'camera',
                 'name': 'new',
                 'thumbnail': '/new/thumb'}
            ]
        }
        self.camera.update(config)
        self.assertEqual(self.camera.thumbnail,
                         'https://rest.test.immedia-semi.com/new/thumb.jpg')

    def test_no_thumbnails(self, mock_sess):
        """Tests that thumbnail is 'None' if none found."""
        mock_sess.return_value = 'foobar'
        self.camera.last_record = ['1']
        config = {
            'name': 'new',
            'camera_id': 1234,
            'network_id': 5678,
            'serial': '12345678',
            'enabled': False,
            'battery_voltage': 90,
            'battery_state': 'ok',
            'temperature': 68,
            'wifi_strength': 4,
            'thumbnail': '',
        }
        self.camera.sync.homescreen = {
            'devices': []
        }
        with self.assertLogs() as logrecord:
            self.camera.update(config)
        self.assertEqual(self.camera.thumbnail, None)
        self.assertEqual(self.camera.last_record, ['1'])
        self.assertEqual(
            logrecord.output,
            ["ERROR:blinkpy.camera:Could not retrieve calibrated temperature.",
             "ERROR:blinkpy.camera:Could not find thumbnail for camera new"]
        )

    def test_no_video_clips(self, mock_sess):
        """Tests that we still proceed with camera setup with no videos."""
        mock_sess.return_value = 'foobar'
        config = {
            'name': 'new',
            'camera_id': 1234,
            'network_id': 5678,
            'serial': '12345678',
            'enabled': False,
            'battery_voltage': 90,
            'battery_state': 'ok',
            'temperature': 68,
            'wifi_strength': 4,
            'thumbnail': '/foobar',
        }
        self.camera.sync.homescreen = {
            'devices': []
        }
        self.camera.update(config, force_cache=True)
        self.assertEqual(self.camera.clip, None)
        self.assertEqual(self.camera.video_from_cache, None)
