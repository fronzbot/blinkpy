"""Test login handler."""

import unittest
from unittest import mock
from blinkpy.login_handler import LoginHandler
import tests.mock_responses as mresp

USERNAME = "foobar"
PASSWORD = "deadbeef"


@mock.patch("blinkpy.helpers.util.Session.send", side_effect=mresp.mocked_session_send)
class TestLoginHandler(unittest.TestCase):
    """Test the LoginHandler class in blinkpy."""

    def setUp(self):
        """Set up Login Handler."""
        self.login_handler = LoginHandler()

    def tearDown(self):
        """Clean up after test."""
        self.login_handler = None

    @mock.patch("blinkpy.login_handler.getpass")
    def test_manual_login(self, getpwd, mock_sess):
        """Check that we can manually use the login() function."""
        getpwd.return_value = PASSWORD
        with mock.patch("builtins.input", return_value=USERNAME):
            self.assertTrue(self.login_handler.check_login())
        self.assertEqual(self.login_handler.data["username"], USERNAME)
        self.assertEqual(self.login_handler.data["password"], PASSWORD)

    def test_no_cred_file(self, mock_sess):
        """Check that we return false when cred file doesn't exist."""
        self.login_handler.cred_file = "/tmp/fake.file"
        self.assertFalse(self.login_handler.check_cred_file())

    @mock.patch("blinkpy.login_handler.isfile")
    def test_exit_on_missing_json(self, mockisfile, mock_sess):
        """Test that we fail on missing json data."""
        self.login_handler.cred_file = "/tmp/fake.file"
        mockisfile.return_value = True
        with mock.patch("builtins.open", mock.mock_open(read_data="{}")):
            self.assertFalse(self.login_handler.check_cred_file())

    @mock.patch("blinkpy.login_handler.json.load")
    @mock.patch("blinkpy.login_handler.isfile")
    def test_cred_file(self, mockisfile, mockjson, mock_sess):
        """Test that loading credential file works."""
        self.login_handler.cred_file = "/tmp/fake.file"
        mockjson.return_value = {"username": "foo", "password": "bar"}
        mockisfile.return_value = True
        with mock.patch("builtins.open", mock.mock_open(read_data="")):
            self.assertTrue(self.login_handler.check_cred_file())
        self.assertEqual(self.login_handler.data["username"], "foo")
        self.assertEqual(self.login_handler.data["password"], "bar")

    def test_bad_response(self, mock_sess):
        """Check bad response from server."""
        self.assertFalse(self.login_handler.validate_response(None, None))

    def test_bad_response_code(self, mock_sess):
        """Check bad response code from server."""
        fake_resp = mresp.MockResponse(None, 404)
        self.assertFalse(self.login_handler.validate_response(None, fake_resp))

    def test_good_response_code(self, mock_sess):
        """Check good response code from server."""
        fake_resp = mresp.MockResponse(None, 200)
        self.assertTrue(self.login_handler.validate_response(None, fake_resp))

    @mock.patch("blinkpy.login_handler.util.gen_uid")
    def test_check_keys_no_persist(self, mock_uid, mock_sess):
        """Check key generation."""
        uid_value = "abc123"
        mock_uid.return_value = "abc123"
        self.login_handler.persist_key = None
        data = self.login_handler.check_keys()
        self.assertEqual(data["uid"], uid_value)
        self.assertEqual(data["notification_key"], uid_value)

    @mock.patch("blinkpy.login_handler.util.gen_uid")
    @mock.patch("blinkpy.login_handler.json.load")
    @mock.patch("blinkpy.login_handler.isfile")
    def test_check_keys_persist(self, mockisfile, mockjson, mock_uid, mock_sess):
        """Check key load from file."""
        uid_value = "abc123"
        mock_file = {"uid": "321cba", "notification_key": "foobar123"}
        mock_uid.return_value = uid_value
        mockjson.return_value = mock_file
        mockisfile.return_value = True
        self.login_handler.persist_key = True
        data = self.login_handler.check_keys()
        self.assertEqual(mock_file["uid"], data["uid"])
        self.assertEqual(mock_file["notification_key"], data["notification_key"])

    def test_check_key_required(self, mock_sess):
        """Check key required method."""
        response_true = {"client": {"verification_required": True}}
        response_false = {"client": {"verification_required": False}}
        response_nokey = {}

        mock_blink = MockBlink(response_nokey)
        self.assertFalse(self.login_handler.check_key_required(mock_blink))

        mock_blink = MockBlink(response_false)
        self.assertFalse(self.login_handler.check_key_required(mock_blink))

        mock_blink = MockBlink(response_true)
        self.assertTrue(self.login_handler.check_key_required(mock_blink))

    @mock.patch("blinkpy.login_handler.api.request_verify")
    def test_send_auth_key(self, mock_req, mock_sess):
        """Check sending of auth key."""
        mock_blink = MockBlink(None)
        mock_req.return_value = mresp.MockResponse({"valid": True}, 200)
        self.assertTrue(self.login_handler.send_auth_key(mock_blink, 1234))
        self.assertTrue(mock_blink.available)

        mock_req.return_value = mresp.MockResponse(None, 200)
        self.assertFalse(self.login_handler.send_auth_key(mock_blink, 1234))

        mock_req.return_value = mresp.MockResponse({}, 200)
        self.assertFalse(self.login_handler.send_auth_key(mock_blink, 1234))

        self.assertTrue(self.login_handler.send_auth_key(mock_blink, None))


class MockBlink:
    """Object to mock basic blink class."""

    def __init__(self, login_response):
        """Initialize mock blink class."""
        self.available = False
        self.login_response = login_response
