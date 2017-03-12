"""Tests camera and system functions."""

import unittest
from unittest import mock
import blinkpy
import tests.mock_responses as mresp

USERNAME = 'foobar'
PASSWORD = 'deadbeef'


class TestBlinkFunctions(unittest.TestCase):
    """Test Blink and BlinkCamera functions in blinkpy."""

    def setUp(self):
        """Set up Blink module."""
        self.blink = blinkpy.Blink(username=USERNAME,
                                   password=PASSWORD)
        (self.region_id, self.region), = mresp.LOGIN_RESPONSE['region'].items()
        self.test_urls = blinkpy.BlinkURLHandler(self.region_id)

    def tearDown(self):
        """Clean up after test."""
        self.blink = None
        self.region = None
        self.region_id = None
        self.test_urls = None

    @mock.patch('blinkpy.blinkpy.requests.post',
                side_effect=mresp.mocked_requests_post)
    @mock.patch('blinkpy.blinkpy.requests.get',
                side_effect=mresp.mocked_requests_get)
    def test_set_motion_detect(self, mock_get, mock_post):
        """Checks if we can set motion detection."""
        self.blink.setup_system()
        self.test_urls = blinkpy.BlinkURLHandler(self.region_id)
        test_cameras = mresp.get_test_cameras(self.test_urls.base_url)
        for camera_name in test_cameras:
            self.blink.cameras[camera_name].set_motion_detect(True)
            self.blink.refresh()
            self.assertEqual(self.blink.cameras[camera_name].armed, True)
            self.blink.cameras[camera_name].set_motion_detect(False)
            self.blink.refresh()
            self.assertEqual(self.blink.cameras[camera_name].armed, False)

    @mock.patch('blinkpy.blinkpy.requests.post',
                side_effect=mresp.mocked_requests_post)
    @mock.patch('blinkpy.blinkpy.requests.get',
                side_effect=mresp.mocked_requests_get)
    def test_last_motion(self, mock_get, mock_post):
        """Checks that we can get the last motion info."""
        self.test_urls = blinkpy.BlinkURLHandler(self.region_id)
        test_events = mresp.RESPONSE['event']
        test_video = dict()
        test_image = dict()
        test_time = dict()
        for event in test_events:
            if event['type'] == 'motion':
                url = self.test_urls.base_url + event['video_url']
                test_video[event['camera_name']] = url
                test_image[event['camera_name']] = url[:-3] + 'jpg'
                test_time[event['camera_name']] = event['created_at']

        self.blink.setup_system()
        for name in self.blink.cameras:
            camera = self.blink.cameras[name]
            self.blink.last_motion()
            if name in test_video:
                self.assertEqual(camera.motion['video'], test_video[name])
            else:
                self.assertEqual(camera.motion, {})
            if name in test_image:
                self.assertEqual(camera.motion['image'], test_image[name])
            else:
                self.assertEqual(camera.motion, {})
            if name in test_video:
                self.assertEqual(camera.motion['time'], test_time[name])
            else:
                self.assertEqual(camera.motion, {})

    @mock.patch('blinkpy.blinkpy.requests.post',
                side_effect=mresp.mocked_requests_post)
    @mock.patch('blinkpy.blinkpy.requests.get',
                side_effect=mresp.mocked_requests_get)
    def test_take_new_picture(self, mock_get, mock_post):
        """Checks if we can take a new picture and retrieve the thumbnail."""
        self.blink.setup_system()
        test_cameras = mresp.get_test_cameras(self.test_urls.base_url)
        test_thumbnail = self.test_urls.base_url + mresp.NEW_THUMBNAIL + '.jpg'
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

    def test_camera_update(self):
        """Checks that the update function is doing the right thing."""
        self.test_urls = blinkpy.BlinkURLHandler('test')
        test_config = mresp.FIRST_CAMERA
        test_camera = blinkpy.blinkpy.BlinkCamera(test_config, self.test_urls)
        test_update = mresp.SECOND_CAMERA
        test_camera.update(test_update)
        test_image_url = self.test_urls.base_url + test_update['thumbnail']
        test_thumbnail = test_image_url + '.jpg'
        test_clip = test_image_url + '.mp4'
        self.assertEqual(test_camera.name, test_update['name'])
        self.assertEqual(test_camera.armed, test_update['armed'])
        self.assertEqual(test_camera.thumbnail, test_thumbnail)
        self.assertEqual(test_camera.clip, test_clip)
        self.assertEqual(test_camera.temperature, test_update['temp'])
        self.assertEqual(test_camera.battery, test_update['battery'])
        self.assertEqual(test_camera.notifications,
                         test_update['notifications'])

    @mock.patch('blinkpy.blinkpy.requests.post',
                side_effect=mresp.mocked_requests_post)
    @mock.patch('blinkpy.blinkpy.requests.get',
                side_effect=mresp.mocked_requests_get)
    def test_camera_thumbs(self, mock_get, mock_post):
        """Checks to see if we can retrieve camera thumbs."""
        self.test_urls = blinkpy.BlinkURLHandler(self.region_id)
        test_cameras = mresp.get_test_cameras(self.test_urls.base_url)
        self.blink.setup_system()
        for name in self.blink.cameras:
            thumb = self.blink.camera_thumbs[name]
            self.assertEqual(test_cameras[name]['thumbnail'], thumb)

    @mock.patch('blinkpy.blinkpy.copyfileobj',
                side_effect=mresp.mocked_copyfileobj)
    @mock.patch('blinkpy.blinkpy.requests.post',
                side_effect=mresp.mocked_requests_post)
    @mock.patch('blinkpy.blinkpy.requests.get',
                side_effect=mresp.mocked_requests_get)
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
