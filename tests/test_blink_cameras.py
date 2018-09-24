"""
Test all camera attributes.

Tests the camera initialization and attributes of
individual BlinkCamera instantiations once the
Blink system is set up.
"""

import unittest
from unittest import mock
from blinkpy import blinkpy
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

        self.blink.urls = blinkpy.BlinkURLHandler('test')
        self.blink.network_id = '0000'

    def tearDown(self):
        """Clean up after test."""
        self.blink = None

    @mock.patch('blinkpy.blinkpy.Blink.camera_config_request',
                return_value=CAMERA_CFG)
    @mock.patch('blinkpy.blinkpy.requests.post',
                side_effect=mresp.mocked_requests_post)
    @mock.patch('blinkpy.blinkpy.requests.get',
                side_effect=mresp.mocked_requests_get)
    def test_camera_properties(self, mock_get, mock_post, mock_cfg):
        """Tests all property set/recall."""
        self.blink.urls = blinkpy.BlinkURLHandler('test')

        self.blink.cameras = {
            'foobar': blinkpy.BlinkCamera(self.camera_config, self.blink)
        }

        for name in self.blink.cameras:
            camera = self.blink.cameras[name]
            camera.update(self.camera_config)
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
        for name in self.blink.cameras:
            camera = self.blink.cameras[name]
            camera.update(camera_config)
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
            camera.update(camera_config)
            self.assertEqual(camera.battery_string, "Unknown")

    def test_camera_case(self):
        """Tests camera case sensitivity."""
        camera_object = blinkpy.BlinkCamera(self.camera_config, self.blink)
        self.blink.cameras['foobar'] = camera_object
        self.assertEqual(camera_object, self.blink.cameras['fOoBaR'])

    @mock.patch('blinkpy.blinkpy.Blink.camera_config_request',
                return_value=CAMERA_CFG)
    def test_camera_attributes(self, mock_cfg):
        """Tests camera attributes."""
        self.blink.urls = blinkpy.BlinkURLHandler('test')

        self.blink.cameras = {
            'foobar': blinkpy.BlinkCamera(self.camera_config, self.blink)
        }

        for name in self.blink.cameras:
            camera = self.blink.cameras[name]
            camera.update(self.camera_config)
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
