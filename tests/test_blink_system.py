"""
Tests the system initialization and attributes of
the main Blink system.  Tests if we properly catch
any communication related errors at startup.
"""

import unittest
from unittest import mock
import blinkpy
import tests.mock_responses as mresp
import helpers.constants as const

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
        """Check that we throw an excpetion when no auth header given."""
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
            blinkpy.blinkpy._request(None, reqtype='bad')

        with self.assertRaises(blinkpy.BlinkAuthenticationException):
            # pylint: disable=protected-access
            blinkpy.blinkpy._request(None, reqtype='post')

    @mock.patch('blinkpy.blinkpy.requests.post',
                side_effect=mresp.mocked_requests_post)
    @mock.patch('blinkpy.blinkpy.requests.get',
                side_effect=mresp.mocked_requests_get)
    def test_full_setup(self, mock_get, mock_post):
        """Check that we can set Blink up properly."""
        self.blink.setup_system()

        # Get all test values
        authtoken = mresp.LOGIN_RESPONSE['authtoken']['authtoken']
        (region_id, region), = mresp.LOGIN_RESPONSE['region'].items()
        host = region_id + '.' + const.BLINK_URL
        network_id = mresp.NETWORKS_RESPONSE['networks'][0]['id']
        account_id = mresp.NETWORKS_RESPONSE['networks'][0]['account_id']
        test_urls = blinkpy.BlinkURLHandler(region_id)
        test_cameras = mresp.get_test_cameras(test_urls.base_url)
        test_camera_id = mresp.get_test_id_table()

        # Check that all links have been set properly
        self.assertEqual(self.blink.region_id, region_id)
        self.assertEqual(self.blink.urls.base_url, test_urls.base_url)
        self.assertEqual(self.blink.urls.home_url, test_urls.home_url)
        self.assertEqual(self.blink.urls.event_url, test_urls.event_url)
        self.assertEqual(self.blink.urls.network_url, test_urls.network_url)
        self.assertEqual(self.blink.urls.networks_url, test_urls.networks_url)

        # Check that all properties have been set after startup
        # pylint: disable=protected-access
        self.assertEqual(self.blink._token, authtoken)
        # pylint: disable=protected-access
        self.assertEqual(self.blink._host, host)
        self.assertEqual(self.blink.network_id, str(network_id))
        self.assertEqual(self.blink.account_id, str(account_id))
        self.assertEqual(self.blink.region, region)

        # Verify we have initialized all the cameras
        self.assertEqual(self.blink.id_table, test_camera_id)
        for camera in test_cameras:
            self.assertTrue(camera in self.blink.cameras)

    @mock.patch('blinkpy.blinkpy.requests.post',
                side_effect=mresp.mocked_requests_post)
    @mock.patch('blinkpy.blinkpy.requests.get',
                side_effect=mresp.mocked_requests_get)
    def test_arm_disarm_system(self, mock_get, mock_post):
        """Check that we can arm/disarm the system"""
        self.blink.setup_system()
        self.blink.arm = False
        self.assertIs(self.blink.arm, False)
        self.blink.arm = True
        self.assertIs(self.blink.arm, True)

    @mock.patch('blinkpy.blinkpy.requests.post',
                side_effect=mresp.mocked_requests_post)
    @mock.patch('blinkpy.blinkpy.requests.get',
                side_effect=mresp.mocked_requests_get)
    def test_check_online_status(self, mock_get, mock_post):
        """Check that we can get our online status."""
        self.blink.setup_system()
        expected_status = const.ONLINE[mresp.RESPONSE['syncmodule']['status']]
        self.assertIs(self.blink.online, expected_status)

    @mock.patch('blinkpy.blinkpy.requests.post',
                side_effect=mresp.mocked_requests_post)
    @mock.patch('blinkpy.blinkpy.requests.get',
                side_effect=mresp.mocked_requests_get)
    def test_setup_backup_subdomain(self, mock_get, mock_post):
        """Check that we can use the 'rest.piri' subdomain."""
        test_urls = blinkpy.BlinkURLHandler('rest.piri')
        with mock.patch('helpers.constants.LOGIN_URL',
                        return_value=const.LOGIN_URL + 'NO'):
            self.blink.setup_system()
        self.assertEqual(self.blink.region_id, 'rest.piri')
        # pylint: disable=protected-access
        self.assertEqual(self.blink._host, 'rest.piri.' + const.BLINK_URL)
        self.assertEqual(self.blink.urls.base_url, test_urls.base_url)
        self.assertEqual(self.blink.urls.home_url, test_urls.home_url)
        self.assertEqual(self.blink.urls.event_url, test_urls.event_url)
        self.assertEqual(self.blink.urls.network_url, test_urls.network_url)
        self.assertEqual(self.blink.urls.networks_url, test_urls.networks_url)
