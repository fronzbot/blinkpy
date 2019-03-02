"""Tests camera and system functions."""
import unittest
from unittest import mock
import logging

from blinkpy import blinkpy
from blinkpy.sync_module import BlinkSyncModule
from blinkpy.helpers.util import create_session, get_time
import tests.mock_responses as mresp

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


@mock.patch('blinkpy.helpers.util.Session.send',
            side_effect=mresp.mocked_session_send)
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
        self.blink.session = create_session()

    def tearDown(self):
        """Clean up after test."""
        self.blink = None

    @mock.patch('blinkpy.blinkpy.api.request_login')
    def test_backup_url(self, req, mock_sess):
        """Test backup login method."""
        json_resp = {
            'authtoken': {'authtoken': 'foobar123'},
            'networks': {'1234': {'name': 'foobar', 'onboarded': True}}
        }
        bad_req = mresp.MockResponse({}, 404)
        new_req = mresp.MockResponse(json_resp, 200)
        req.side_effect = [
            bad_req,
            bad_req,
            new_req
        ]
        self.blink.login_request(['test1', 'test2', 'test3'])
        # pylint: disable=protected-access
        self.assertEqual(self.blink._login_url, 'test3')

        req.side_effect = [
            bad_req,
            new_req,
            bad_req
        ]
        self.blink.login_request(['test1', 'test2', 'test3'])
        # pylint: disable=protected-access
        self.assertEqual(self.blink._login_url, 'test2')

    def test_merge_cameras(self, mock_sess):
        """Test merge camera functionality."""
        first_dict = {'foo': 'bar', 'test': 123}
        next_dict = {'foobar': 456, 'bar': 'foo'}
        self.blink.sync['foo'] = BlinkSyncModule(self.blink, 'foo', 1, [])
        self.blink.sync['bar'] = BlinkSyncModule(self.blink, 'bar', 2, [])
        self.blink.sync['foo'].cameras = first_dict
        self.blink.sync['bar'].cameras = next_dict
        result = self.blink.merge_cameras()
        expected = {'foo': 'bar', 'test': 123, 'foobar': 456, 'bar': 'foo'}
        self.assertEqual(expected, result)

    @mock.patch('blinkpy.blinkpy.api.request_videos')
    def test_download_video_exit(self, mock_req, mock_sess):
        """Test we exit method when provided bad response."""
        blink = blinkpy.Blink()
        # pylint: disable=protected-access
        blinkpy._LOGGER.setLevel(logging.DEBUG)
        blink.last_refresh = 0
        mock_req.return_value = {}
        formatted_date = get_time(blink.last_refresh)
        expected_log = [
            "INFO:blinkpy.blinkpy:Retrieving videos since {}".format(
                formatted_date),
            "DEBUG:blinkpy.blinkpy:Processing page 1",
            "INFO:blinkpy.blinkpy:No videos found on page 1. Exiting."
        ]
        with self.assertLogs() as dl_log:
            blink.download_videos('/tmp')
        self.assertEqual(dl_log.output, expected_log)

    @mock.patch('blinkpy.blinkpy.api.request_videos')
    def test_parse_downloaded_items(self, mock_req, mock_sess):
        """Test ability to parse downloaded items list."""
        blink = blinkpy.Blink()
        # pylint: disable=protected-access
        blinkpy._LOGGER.setLevel(logging.DEBUG)
        generic_entry = {
            'created_at': '1970',
            'camera_name': 'foo',
            'deleted': True,
            'address': '/bar.mp4'
        }
        result = [generic_entry]
        mock_req.return_value = {'videos': result}
        blink.last_refresh = 0
        formatted_date = get_time(blink.last_refresh)
        expected_log = [
            "INFO:blinkpy.blinkpy:Retrieving videos since {}".format(
                formatted_date),
            "DEBUG:blinkpy.blinkpy:Processing page 1",
            "DEBUG:blinkpy.blinkpy:foo: /bar.mp4 is marked as deleted."
        ]
        with self.assertLogs() as dl_log:
            blink.download_videos('/tmp', stop=2)
        self.assertEqual(dl_log.output, expected_log)

    @mock.patch('blinkpy.blinkpy.api.request_videos')
    def test_parse_camera_not_in_list(self, mock_req, mock_sess):
        """Test ability to parse downloaded items list."""
        blink = blinkpy.Blink()
        # pylint: disable=protected-access
        blinkpy._LOGGER.setLevel(logging.DEBUG)
        generic_entry = {
            'created_at': '1970',
            'camera_name': 'foo',
            'deleted': True,
            'address': '/bar.mp4'
        }
        result = [generic_entry]
        mock_req.return_value = {'videos': result}
        blink.last_refresh = 0
        formatted_date = get_time(blink.last_refresh)
        expected_log = [
            "INFO:blinkpy.blinkpy:Retrieving videos since {}".format(
                formatted_date),
            "DEBUG:blinkpy.blinkpy:Processing page 1",
            "DEBUG:blinkpy.blinkpy:Skipping videos for foo."
        ]
        with self.assertLogs() as dl_log:
            blink.download_videos('/tmp', camera='bar', stop=2)
        self.assertEqual(dl_log.output, expected_log)
