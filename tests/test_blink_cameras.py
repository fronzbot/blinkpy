"""
Tests the camera initialization and attributes of
individual BlinkCamera instantiations.
"""

import unittest
from unittest import mock
import blinkpy
import tests.mock_responses as mresp

USERNAME = 'foobar'
PASSWORD = 'deadbeef'


class TestBlinkCameraSetup(unittest.TestCase):
    """Test the Blink class in blinkpy."""

    def setUp(self):
        """Set up Blink module."""
        self.blink = blinkpy.Blink(username=USERNAME,
                                   password=PASSWORD)

    def tearDown(self):
        """Clean up after test."""
        self.blink = None

    @mock.patch('blinkpy.blinkpy.requests.post',
                side_effect=mresp.mocked_requests_post)
    @mock.patch('blinkpy.blinkpy.requests.get',
                side_effect=mresp.mocked_requests_get)
    def test_camera_properties(self, mock_get, mock_post):
        """Tests all property set/recall."""
        test_value = 'foobar'
        test_region_id = list(mresp.LOGIN_RESPONSE['region'].keys())[0]
        self.blink.setup_system()
        for name in self.blink.cameras:
            camera = self.blink.cameras[name]
            camera.name = test_value
            camera.clip = test_value + '.mp4'
            camera.thumbnail = test_value + '.jpg'
            camera.temperature = 10
            camera.battery = 0
            camera.notifications = 100
            camera.image_link = test_value + '/image.jpg'
            camera.arm_link = test_value + '/arm'
            camera.header = {'foo': 'bar'}
            camera.motion = {'bar': 'foo'}
            self.assertEqual(camera.clip, test_value + '.mp4')
            self.assertEqual(camera.name, test_value)
            self.assertEqual(camera.thumbnail, test_value + '.jpg')
            self.assertEqual(camera.temperature, 10)
            self.assertEqual(camera.battery, 0)
            self.assertEqual(camera.notifications, 100)
            self.assertEqual(camera.image_link, test_value + '/image.jpg')
            self.assertEqual(camera.arm_link, test_value + '/arm')
            self.assertEqual(camera.header, {'foo': 'bar'})
            self.assertEqual(camera.motion, {'bar': 'foo'})
            self.assertEqual(camera.region_id, test_region_id)

    @mock.patch('blinkpy.blinkpy.requests.post',
                side_effect=mresp.mocked_requests_post)
    @mock.patch('blinkpy.blinkpy.requests.get',
                side_effect=mresp.mocked_requests_get)
    def test_camera_values_from_setup(self, mock_get, mock_post):
        """Tests all property values after camera setup."""
        self.blink.setup_system()

        # Get expected test values
        test_network_id = str(mresp.NETWORKS_RESPONSE['networks'][0]['id'])
        # pylint: disable=unused-variable
        (region_id, region), = mresp.LOGIN_RESPONSE['region'].items()
        # pylint: disable=protected-access
        expected_header = self.blink._auth_header
        test_urls = blinkpy.BlinkURLHandler(region_id)

        test_cameras = mresp.get_test_cameras(test_urls.base_url)
        test_net_id_url = test_urls.network_url + test_network_id
        for name in self.blink.cameras:
            camera = self.blink.cameras[name]
            self.assertEqual(name, camera.name)
            if name in test_cameras:
                self.assertEqual(camera.id,
                                 test_cameras[name]['device_id'])
                self.assertEqual(camera.armed,
                                 test_cameras[name]['armed'])
                self.assertEqual(camera.thumbnail,
                                 test_cameras[name]['thumbnail'])
                self.assertEqual(camera.temperature,
                                 test_cameras[name]['temperature'])
                self.assertEqual(camera.battery,
                                 test_cameras[name]['battery'])
                self.assertEqual(camera.notifications,
                                 test_cameras[name]['notifications'])
            else:
                self.fail("Camera wasn't initialized: " + name)

            expected_arm_link = test_net_id_url + '/camera/' + camera.id + '/'
            expected_image_link = expected_arm_link + 'thumbnail'
            self.assertEqual(camera.image_link, expected_image_link)
            self.assertEqual(camera.arm_link, expected_arm_link)
            self.assertEqual(camera.header, expected_header)
