"""
Test full system.

Tests the system initialization and attributes of
the main Blink system.  Tests if we properly catch
any communication related errors at startup.
"""

import unittest
from unittest import mock
from blinkpy import blinkpy as blinkpy
import tests.mock_responses as mresp

USERNAME = 'foobar'
PASSWORD = 'deadbeef'


class TestBlinkSetup(unittest.TestCase):
    """Test the Blink class in blinkpy."""

    def setUp(self):
        """Set up Blink module."""
        self.blink_no_cred = blinkpy.Blink()
        self.blink = blinkpy.Blink(username=USERNAME,
                                   password=PASSWORD)

    def tearDown(self):
        """Clean up after test."""
        self.blink = None
        self.blink_no_cred = None

    def test_initialization(self):
        """Verify we can initialize blink."""
        # pylint: disable=protected-access
        self.assertEqual(self.blink._username, USERNAME)
        # pylint: disable=protected-access
        self.assertEqual(self.blink._password, PASSWORD)

    def test_no_credentials(self):
        """Check that we throw an exception when no username/password."""
        with self.assertRaises(blinkpy.BlinkAuthenticationException):
            self.blink_no_cred.get_auth_token()
        with self.assertRaises(blinkpy.BlinkAuthenticationException):
            self.blink_no_cred.setup_system()
        # pylint: disable=protected-access
        self.blink_no_cred._username = USERNAME
        with self.assertRaises(blinkpy.BlinkAuthenticationException):
            self.blink_no_cred.get_auth_token()

    def test_no_auth_header(self):
        """Check that we throw an exception when no auth header given."""
        # pylint: disable=unused-variable
        (region_id, region), = mresp.LOGIN_RESPONSE['region'].items()
        self.blink.urls = blinkpy.BlinkURLHandler(region_id)
        with self.assertRaises(blinkpy.BlinkException):
            self.blink.get_ids()
        with self.assertRaises(blinkpy.BlinkException):
            self.blink.get_summary()

    @mock.patch('blinkpy.blinkpy.getpass.getpass')
    def test_manual_login(self, getpwd):
        """Check that we can manually use the login() function."""
        getpwd.return_value = PASSWORD
        with mock.patch('builtins.input', return_value=USERNAME):
            self.blink_no_cred.login()
        # pylint: disable=protected-access
        self.assertEqual(self.blink_no_cred._username, USERNAME)
        # pylint: disable=protected-access
        self.assertEqual(self.blink_no_cred._password, PASSWORD)

    @mock.patch('blinkpy.blinkpy.requests.post',
                side_effect=mresp.mocked_requests_post)
    @mock.patch('blinkpy.blinkpy.requests.get',
                side_effect=mresp.mocked_requests_get)
    def test_bad_request(self, mock_get, mock_post):
        """Check that we raise an Exception with a bad request."""
        with self.assertRaises(blinkpy.BlinkException):
            # pylint: disable=protected-access
            blinkpy._request(None, reqtype='bad')

        with self.assertRaises(blinkpy.BlinkAuthenticationException):
            # pylint: disable=protected-access
            blinkpy._request(None, reqtype='post', is_retry=True)

    @mock.patch('blinkpy.blinkpy.requests.post',
                side_effect=mresp.mocked_requests_post)
    @mock.patch('blinkpy.blinkpy.requests.get',
                side_effect=mresp.mocked_requests_get)
    def test_authentication(self, mock_get, mock_post):
        """Check that we can authenticate Blink up properly."""
        authtoken = self.blink.get_auth_token()['TOKEN_AUTH']
        expected = mresp.LOGIN_RESPONSE['authtoken']['authtoken']
        self.assertEqual(authtoken, expected)

    @mock.patch('blinkpy.blinkpy.requests.post',
                side_effect=mresp.mocked_requests_post)
    @mock.patch('blinkpy.blinkpy.requests.get',
                side_effect=mresp.mocked_requests_get)
    def test_reauthorization_attempt(self, mock_get, mock_post):
        """Check that we can reauthorize after first unsuccessful attempt."""
        original_header = self.blink.get_auth_token()
        # pylint: disable=protected-access
        bad_header = {'Host': self.blink._host, 'TOKEN_AUTH': 'BADTOKEN'}
        # pylint: disable=protected-access
        self.blink._auth_header = bad_header
        # pylint: disable=protected-access
        self.assertEqual(self.blink._auth_header, bad_header)
        self.blink.get_summary()
        # pylint: disable=protected-access
        self.assertEqual(self.blink._auth_header, original_header)
