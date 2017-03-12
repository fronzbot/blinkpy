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

        test_cameras = dict()
        for element in mresp.RESPONSE['devices']:
            if ('device_type' in element and
                    element['device_type'] == 'camera'):
                test_cameras[element['name']] = {
                    'device_id': str(element['device_id']),
                    'armed': element['armed'],
                    'thumbnail': (test_urls.base_url +
                                  element['thumbnail'] + '.jpg'),
                    'temperature': element['temp'],
                    'battery': element['battery'],
                    'notifications': element['notifications']
                }
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
