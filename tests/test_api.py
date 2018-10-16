"""Test various api functions."""

import unittest
from blinkpy import api
from blinkpy.blinkpy import Blink
from blinkpy.helpers.util import create_session


class TestBlinkAPI(unittest.TestCase):
    """Test the blink api module."""

    def setUp(self):
        """Initialize the blink module."""
        self.blink = Blink()
        self.blink.session = create_session()
        # pylint: disable=protected-access
        self.blink._auth_header = {}

    def tearDown(self):
        """Tear down blink module."""
        self.blink = None

    def test_http_req_connect_error(self):
        """Test http_get error condition."""
        expected = ("ERROR:blinkpy.helpers.util:"
                    "Cannot connect to server. Possible outage.")
        with self.assertLogs() as getlog:
            api.http_get(self.blink, 'http://notreal.fake')
        with self.assertLogs() as postlog:
            api.http_post(self.blink, 'http://notreal.fake')
        self.assertEqual(getlog.output, [expected])
        self.assertEqual(postlog.output, [expected])
