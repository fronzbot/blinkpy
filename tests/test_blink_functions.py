"""Tests camera and system functions."""
import unittest
from unittest import mock

from requests import Request

from blinkpy import blinkpy
from blinkpy.sync_module import BlinkSyncModule
from blinkpy.helpers.util import create_session
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

    @mock.patch('blinkpy.blinkpy.api.http_req')
    def test_backup_url(self, req, mock_sess):
        """Test backup login method."""
        fake_req = Request('POST', 'http://wrong.url').prepare()
        req.side_effect = [
            mresp.mocked_session_send(fake_req),
            {'authtoken': {'authtoken': 'foobar123'},
             'networks': {'1234': {'name': 'foobar', 'onboarded': True}}}
        ]
        self.blink.get_auth_token()
        self.assertEqual(self.blink.region_id, 'piri')
        self.assertEqual(self.blink.region, 'UNKNOWN')
        # pylint: disable=protected-access
        self.assertEqual(self.blink._token, 'foobar123')

    def test_merge_cameras(self, mock_sess):
        """Test merge camera functionality."""
        first_dict = {'foo': 'bar', 'test': 123}
        next_dict = {'foobar': 456, 'bar': 'foo'}
        self.blink.sync['foo'] = BlinkSyncModule(self.blink, 'foo', 1)
        self.blink.sync['bar'] = BlinkSyncModule(self.blink, 'bar', 2)
        self.blink.sync['foo'].cameras = first_dict
        self.blink.sync['bar'].cameras = next_dict
        result = self.blink.merge_cameras()
        expected = {'foo': 'bar', 'test': 123, 'foobar': 456, 'bar': 'foo'}
        self.assertEqual(expected, result)
