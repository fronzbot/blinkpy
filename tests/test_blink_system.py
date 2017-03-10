import requests
import unittest
import blinkpy
from unittest import mock
import constants as const

USERNAME = 'foobar'
PASSWORD = 'deadbeef'

class TestBlinkSetup(unittest.TestCase):
    """Test the Blink class in blinkpy."""
    def test_initialization(self):
        """Verify we can initialize blink."""
        blink = blinkpy.Blink(username=USERNAME, password=PASSWORD)
        self.assertEqual(blink._username, USERNAME)
        self.assertEqual(blink._password, PASSWORD)

    def test_no_credentials(self):
        """Check that we throw an exception when no username/password."""
        blink = blinkpy.Blink()
        with self.assertRaises(blinkpy.BlinkAuthenticationException):
            blink.get_auth_token()
        with self.assertRaises(blinkpy.BlinkAuthenticationException):
            blink.setup_system()

    def test_no_auth_header(self):
        """Check that we throw an excpetion when no auth header given."""
        blink = blinkpy.Blink(username=USERNAME, password=PASSWORD)
        with self.assertRaises(blinkpy.BlinkException):
            blink.get_ids()
    
    @mock.patch('blinkpy.getpass.getpass')
    def test_manual_login(self, getpwd):
        """Check that we can manually use the login() function."""
        blink = blinkpy.Blink()
        getpwd.return_value = PASSWORD
        with mock.patch('builtins.input', return_value=USERNAME):
            blink.login()
        self.assertEqual(blink._username, USERNAME)
        self.assertEqual(blink._password, PASSWORD)

    # NEXT NEED ACTUAL REQUEST TESTS
        