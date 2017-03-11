import requests
import unittest
from unittest import mock
import blinkpy
import tests.mock_responses as mresp
import constants as const

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
        self.assertEqual(self.blink._username, USERNAME)
        self.assertEqual(self.blink._password, PASSWORD)

    def test_no_credentials(self):
        """Check that we throw an exception when no username/password."""
        with self.assertRaises(blinkpy.BlinkAuthenticationException):
            self.blink_no_cred.get_auth_token()
        with self.assertRaises(blinkpy.BlinkAuthenticationException):
            self.blink_no_cred.setup_system()

    def test_no_auth_header(self):
        """Check that we throw an excpetion when no auth header given."""
        (region_id, region), = mresp.LOGIN_RESPONSE['region'].items()
        self.blink.urls = blinkpy.BlinkURLHandler(region_id)
        with self.assertRaises(blinkpy.BlinkException):
            self.blink.get_ids()
    
    @mock.patch('blinkpy.getpass.getpass')
    def test_manual_login(self, getpwd):
        """Check that we can manually use the login() function."""
        getpwd.return_value = PASSWORD
        with mock.patch('builtins.input', return_value=USERNAME):
            self.blink_no_cred.login()
        self.assertEqual(self.blink_no_cred._username, USERNAME)
        self.assertEqual(self.blink_no_cred._password, PASSWORD)

    @mock.patch('blinkpy.requests.post', side_effect=mresp.mocked_requests_post)
    @mock.patch('blinkpy.requests.get', side_effect=mresp.mocked_requests_get)
    def test_full_setup(self, mock_get, mock_post):
        """Check that we can set Blink up properly."""
        self.blink.setup_system()
        
        # Get all test values
        authtoken = mresp.LOGIN_RESPONSE['authtoken']['authtoken']
        (region_id, region), = mresp.LOGIN_RESPONSE['region'].items()
        host = region_id + '.' + const.BLINK_URL
        network_id = mresp.NETWORKS_RESPONSE['networks'][0]['id']
        account_id = mresp.NETWORKS_RESPONSE['networks'][0]['account_id']
        TestURLs = blinkpy.BlinkURLHandler(region_id)
        TestCameras = list()
        TestCameraID = dict()
        for element in mresp.RESPONSE['devices']:
            if 'device_type' in element and element['device_type'] == 'camera':
                TestCameras.append(element['name'])
                TestCameraID[str(element['device_id'])] = element['name']

        # Check that all links have been set properly
        self.assertEqual(self.blink.region_id, region_id)
        self.assertEqual(self.blink.urls.base_url, TestURLs.base_url)
        self.assertEqual(self.blink.urls.home_url, TestURLs.home_url)
        self.assertEqual(self.blink.urls.event_url, TestURLs.event_url)
        self.assertEqual(self.blink.urls.network_url, TestURLs.network_url)
        self.assertEqual(self.blink.urls.networks_url, TestURLs.networks_url)

        # Check that all properties have been set after startup
        self.assertEqual(self.blink._token, authtoken)
        self.assertEqual(self.blink._host, host)
        self.assertEqual(self.blink.network_id, str(network_id))
        self.assertEqual(self.blink.account_id, str(account_id))
        self.assertEqual(self.blink.region, region)

        # Verify we have initialized all the cameras
        self.assertEqual(self.blink.id_table, TestCameraID)
        for camera in TestCameras:
            self.assertTrue(camera in self.blink.cameras)

    @mock.patch('blinkpy.requests.post', side_effect=mresp.mocked_requests_post)
    @mock.patch('blinkpy.requests.get', side_effect=mresp.mocked_requests_get)
    def test_arm_disarm_system(self, mock_get, mock_post):
        """Check that we can arm/disarm the system"""
        self.blink.setup_system()
        self.blink.arm = False
        self.assertIs(self.blink.arm, False)
        self.blink.arm = True
        self.assertIs(self.blink.arm, True)

    @mock.patch('blinkpy.requests.post', side_effect=mresp.mocked_requests_post)
    @mock.patch('blinkpy.requests.get', side_effect=mresp.mocked_requests_get)
    def test_check_online_status(self, mock_get, mock_post):
        """Check that we can get our online status."""
        self.blink.setup_system()
        expected_status = const.ONLINE[mresp.RESPONSE['syncmodule']['status']]
        self.assertIs(self.blink.online, expected_status)
