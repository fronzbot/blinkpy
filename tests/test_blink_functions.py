"""Tests camera and system functions."""

import unittest
from unittest import mock
import random
import pytest
from blinkpy import blinkpy as blinkpy
import tests.mock_responses as mresp

USERNAME = 'foobar'
PASSWORD = 'deadbeef'


class TestBlinkFunctions(unittest.TestCase):
    """Test Blink and BlinkCamera functions in blinkpy."""

    def setUp(self):
        """Set up Blink module."""
        self.blink = blinkpy.Blink(username=USERNAME,
                                   password=PASSWORD)
        self.blink.get_auth_token()
        self.urls = blinkpy.BlinkURLHandler('test')
        self.config = {
            'device_id': 1111,
            'name': 'foobar',
            'armed': False,
            'thumbnail': '/test',
            'video': '/test.mp4',
            'temp': 80,
            'battery': 3,
            'notifications': 2,
            'region_id': 'test'
        }
        self.camera = blinkpy.BlinkCamera(self.config, self.blink)

    def tearDown(self):
        """Clean up after test."""
        self.blink = None
        self.urls = None
        self.config = {}
        self.camera = None

    @mock.patch('blinkpy.blinkpy.requests.post',
                side_effect=mresp.mocked_requests_post)
    @mock.patch('blinkpy.blinkpy.requests.get',
                side_effect=mresp.mocked_requests_get)
    @pytest.mark.skip(reason="Need to simplify")
    def test_take_new_picture(self, mock_get, mock_post):
        """Checks if we can take a new picture and retrieve the thumbnail."""
        self.blink.setup_system()
        test_cameras = {}  # mresp.get_test_cameras(self.test_urls.base_url)
        test_thumbnail = ''
        # self.test_urls.base_url + mresp.NEW_THUMBNAIL + '.jpg'
        # Snap picture for each camera and check new thumb
        for camera_name in test_cameras:
            camera = self.blink.cameras[camera_name]
            camera.snap_picture()
            camera.image_refresh()
            self.assertEqual(camera.thumbnail, test_thumbnail)

        # Manually set thumbnail, and then globally refresh and check
        for camera_name in test_cameras:
            camera = self.blink.cameras[camera_name]
            camera.thumbnail = 'Testing'
            self.assertEqual(camera.thumbnail, 'Testing')

        self.blink.refresh()
        for camera_name in test_cameras:
            camera = self.blink.cameras[camera_name]
            self.assertEqual(camera.thumbnail, test_thumbnail)

    @mock.patch('blinkpy.blinkpy.requests.post',
                side_effect=mresp.mocked_requests_post)
    @mock.patch('blinkpy.blinkpy.requests.get',
                side_effect=mresp.mocked_requests_get)
    @pytest.mark.skip(reason="Need to simplify")
    def test_image_with_bad_data(self, mock_get, mock_post):
        """Checks for handling of bad keys."""
        self.blink.setup_system()
        for camera_name in self.blink.cameras:
            camera = self.blink.cameras[camera_name]
            camera.snap_picture()
            camera.urls.home_url = "use_bad_response"
            self.assertEqual(camera.image_refresh(), None)

    @mock.patch('blinkpy.blinkpy.requests.post',
                side_effect=mresp.mocked_requests_post)
    @mock.patch('blinkpy.blinkpy.requests.get',
                side_effect=mresp.mocked_requests_get)
    @pytest.mark.skip(reason="Need to simplify")
    def test_camera_random_case(self, mock_get, mock_post):
        """Checks for case of camera name."""
        self.blink.setup_system()
        for camera_name in self.blink.cameras:

            rand_name = camera_name
            # Make sure we never pass this test if rand_name = camera_name
            while rand_name == camera_name:
                rand_name = ''.join(
                    random.choice(
                        (str.upper, str.lower)
                    )(x) for x in camera_name)

            self.assertEqual(self.blink.cameras[camera_name].name,
                             self.blink.cameras[rand_name].name)

    @mock.patch('blinkpy.blinkpy.requests.post',
                side_effect=mresp.mocked_requests_post)
    @mock.patch('blinkpy.blinkpy.requests.get',
                side_effect=mresp.mocked_requests_get)
    @pytest.mark.skip(reason="Need to simplify")
    def test_camera_thumbs(self, mock_get, mock_post):
        """Checks to see if we can retrieve camera thumbs."""
        test_cameras = {}  # mresp.get_test_cameras(self.test_urls.base_url)
        self.blink.setup_system()
        for name in self.blink.cameras:
            thumb = self.blink.camera_thumbs[name]
            self.assertEqual(test_cameras[name]['thumbnail'], thumb)


# pylint: disable=pointless-string-statement
'''
    @mock.patch('blinkpy.blinkpy.copyfileobj',
                side_effect=mresp.mocked_copyfileobj)
    @mock.patch('blinkpy.blinkpy.requests.post',
                side_effect=mresp.mocked_requests_post)
    @mock.patch('blinkpy.blinkpy.requests.get',
                side_effect=mresp.mocked_requests_get)
    @pytest.mark.skip(reason="Need to simplify")
    def test_image_to_file(self, mock_get, mock_post, mock_copyfileobj):
        """Checks that we can write an image to file."""
        self.blink.setup_system()
        cameras = self.blink.cameras
        filename = '/tmp/test.jpg'
        test_files = list()
        for camera_name in cameras:
            camera = cameras[camera_name]
            test_files.append(mresp.MOCK_BYTES)
            mock_fh = mock.mock_open()
            with mock.patch('builtins.open', mock_fh, create=True):
                camera.image_to_file(camera_name + filename)
            mock_fh.assert_called_once_with(camera_name + filename, 'wb')
        self.assertEqual(test_files, mresp.FAKE_FILES)
'''
