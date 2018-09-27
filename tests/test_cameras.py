"""
Test all camera attributes.

Tests the camera initialization and attributes of
individual BlinkCamera instantiations once the
Blink system is set up.
"""

import unittest
from unittest import mock
from blinkpy import blinkpy
from blinkpy.helpers.util import BlinkURLHandler
from blinkpy.sync_module import BlinkSyncModule
from blinkpy.camera import BlinkCamera
from blinkpy.helpers.constants import BLINK_URL
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


class TestBlinkCameraSetup(unittest.TestCase):
    """Test the Blink class in blinkpy."""

    def setUp(self):
        """Set up Blink module."""
        self.blink = blinkpy.Blink(username=USERNAME,
                                   password=PASSWORD)
        self.camera_config = {
            'device_id': 1111,
            'name': 'foobar',
            'armed': False,
            'active': 'disarmed',
            'thumbnail': '/test/image',
            'video': '/test/clip/clip.mp4',
            'temp': 70,
            'battery': 3,
            'notifications': 2,
            'region_id': 'test'
        }

        header = {
            'Host': 'abc.zxc',
            'TOKEN_AUTH': mresp.LOGIN_RESPONSE['authtoken']['authtoken']
        }
        self.blink.urls = BlinkURLHandler('test')
        self.blink.network_id = '0000'
        self.sync = BlinkSyncModule(self.blink, header, self.blink.urls)

    def tearDown(self):
        """Clean up after test."""
        self.blink = None

    @mock.patch('blinkpy.sync_module.BlinkSyncModule.camera_config_request',
                return_value=CAMERA_CFG)
    @mock.patch('blinkpy.helpers.util.requests.post',
                side_effect=mresp.mocked_requests_post)
    @mock.patch('blinkpy.helpers.util.requests.get',
                side_effect=mresp.mocked_requests_get)
    def test_camera_properties(self, mock_get, mock_post, mock_cfg):
        """Tests all property set/recall."""
        self.blink.urls = BlinkURLHandler('test')

        self.sync.cameras = {
            'foobar': BlinkCamera(self.camera_config, self.sync)
        }

        for name in self.sync.cameras:
            camera = self.sync.cameras[name]
            camera.update(self.camera_config, skip_cache=True)
            self.assertEqual(camera.id, '1111')
            self.assertEqual(camera.name, 'foobar')
            self.assertEqual(camera.armed, False)
            self.assertEqual(
                camera.thumbnail,
                "https://rest.test.{}/test/image.jpg".format(BLINK_URL)
            )
            self.assertEqual(
                camera.clip,
                "https://rest.test.{}/test/clip/clip.mp4".format(BLINK_URL)
            )
            self.assertEqual(camera.temperature, 68)
            self.assertEqual(camera.temperature_c, 20.0)
            self.assertEqual(camera.battery, 50)
            self.assertEqual(camera.battery_string, "OK")
            self.assertEqual(camera.notifications, 2)
            self.assertEqual(camera.region_id, 'test')
            self.assertEqual(camera.motion_enabled, True)
            self.assertEqual(camera.wifi_strength, -30)

        camera_config = self.camera_config
        camera_config['active'] = 'armed'
        camera_config['thumbnail'] = '/test2/image'
        camera_config['video'] = '/test2/clip.mp4'
        camera_config['temp'] = 60
        camera_config['battery'] = 0
        camera_config['notifications'] = 4
        for name in self.sync.cameras:
            camera = self.sync.cameras[name]
            camera.update(camera_config, skip_cache=True)
            self.assertEqual(camera.armed, True)
            self.assertEqual(
                camera.thumbnail,
                "https://rest.test.{}/test2/image.jpg".format(BLINK_URL)
            )
            self.assertEqual(
                camera.clip,
                "https://rest.test.{}/test2/clip.mp4".format(BLINK_URL)
            )
            self.assertEqual(camera.temperature, 68)
            self.assertEqual(camera.battery, 50)
            self.assertEqual(camera.battery_string, "Low")
            self.assertEqual(camera.notifications, 4)
            camera_config['battery'] = -10
            camera.update(camera_config, skip_cache=True)
            self.assertEqual(camera.battery_string, "Unknown")

    def test_camera_case(self):
        """Tests camera case sensitivity."""
        camera_object = BlinkCamera(self.camera_config, self.sync)
        self.sync.cameras['foobar'] = camera_object
        self.assertEqual(camera_object, self.sync.cameras['fOoBaR'])

    @mock.patch('blinkpy.sync_module.BlinkSyncModule.camera_config_request',
                return_value=CAMERA_CFG)
    def test_camera_attributes(self, mock_cfg):
        """Tests camera attributes."""
        self.blink.urls = BlinkURLHandler('test')

        self.sync.cameras = {
            'foobar': BlinkCamera(self.camera_config, self.sync)
        }

        for name in self.sync.cameras:
            camera = self.sync.cameras[name]
            camera.update(self.camera_config, skip_cache=True)
            camera_attr = camera.attributes
            self.assertEqual(camera_attr['device_id'], '1111')
            self.assertEqual(camera_attr['name'], 'foobar')
            self.assertEqual(camera_attr['armed'], False)
            self.assertEqual(
                camera_attr['thumbnail'],
                "https://rest.test.{}/test/image.jpg".format(BLINK_URL)
            )
            self.assertEqual(
                camera_attr['video'],
                "https://rest.test.{}/test/clip/clip.mp4".format(BLINK_URL)
            )
            self.assertEqual(camera_attr['temperature'], 68)
            self.assertEqual(camera_attr['temperature_c'], 20.0)
            self.assertEqual(camera_attr['battery'], 50)
            self.assertEqual(camera_attr['notifications'], 2)
            self.assertEqual(camera_attr['network_id'], '0000')
            self.assertEqual(camera_attr['motion_enabled'], True)
            self.assertEqual(camera_attr['wifi_strength'], -30)

    @mock.patch('blinkpy.camera.BlinkCamera.image_refresh',
                side_effect='refresh/url')
    @mock.patch('blinkpy.helpers.util.requests.get',
                side_effect=mresp.mocked_requests_get)
    def test_camera_cache(self, req, img_refresh):
        """Tests camera cache."""
        update_vals = {
            'name': 'foobar',
            'active': 'disabled',
            'video': '/clip.mp4',
            'thumbnail': '/image',
            'battery': 3,
            'notifications': 1,
        }
        self.sync.cameras = {
            'foobar': BlinkCamera(self.camera_config, self.sync)
        }

        test_image = 'https://rest.test.immedia-semi.com/image.jpg'
        test_clip = 'https://rest.test.immedia-semi.com/clip.mp4'

        for name, camera in self.sync.cameras.items():
            # Check that no cache returns None
            self.assertEqual(camera.name, name)
            self.assertEqual(camera.image_from_cache, None)
            self.assertEqual(camera.video_from_cache, None)

            # Now, call an update with a new thumbnail to see if we update
            self.sync.records = []
            # pylint: disable=protected-access
            camera.update(update_vals)
            self.assertEqual(camera.thumbnail, test_image)
            self.assertEqual(camera.image_from_cache.status_code, 200)

            # Now update the clip
            self.sync.record_dates = {camera.name: ['7', '1', '4', '3']}
            self.assertEqual(camera.last_record, list())
            camera.update(update_vals)
            self.assertEqual(camera.clip, test_clip)
            self.assertEqual(camera.last_record, list('7'))
            # First update should be false
            self.assertEqual(camera.motion_detected, False)
            self.sync.record_dates[camera.name].append('88')
            camera.update(update_vals)
            self.assertEqual(camera.last_record, ['88', '7'])
            self.assertEqual(camera.motion_detected, True)
            self.assertEqual(camera.video_from_cache.status_code, 200)
            # Next update shouldn't change records, and motion_dected=False
            camera.update(update_vals)
            self.assertEqual(camera.motion_detected, False)
            self.assertEqual(camera.video_from_cache.status_code, 200)
