"""Test various api functions."""

import unittest
from unittest import mock
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

    @mock.patch("blinkpy.blinkpy.Blink.get_auth_token")
    def test_http_req_connect_error(self, mock_auth):
        """Test http_get error condition."""
        mock_auth.return_value = {"foo": "bar"}
        firstlog = (
            "INFO:blinkpy.helpers.util:" "Cannot connect to server with url {}."
        ).format("http://notreal.fake")
        nextlog = (
            "INFO:blinkpy.helpers.util:"
            "Auth token expired, attempting reauthorization."
        )
        lastlog = (
            "ERROR:blinkpy.helpers.util:"
            "Endpoint {} failed. Possible issue with "
            "Blink servers."
        ).format("http://notreal.fake")
        expected = [firstlog, nextlog, firstlog, lastlog]
        with self.assertLogs() as getlog:
            api.http_get(self.blink, "http://notreal.fake")
        with self.assertLogs() as postlog:
            api.http_post(self.blink, "http://notreal.fake")
        self.assertEqual(getlog.output, expected)
        self.assertEqual(postlog.output, expected)
