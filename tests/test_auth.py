"""Test login handler."""

import unittest
from unittest import mock
from requests import exceptions
from blinkpy.auth import (
    Auth,
    LoginError,
    TokenRefreshFailed,
    BlinkBadResponse,
    UnauthorizedError,
)
import blinkpy.helpers.constants as const
import tests.mock_responses as mresp

USERNAME = "foobar"
PASSWORD = "deadbeef"


class TestAuth(unittest.TestCase):
    """Test the Auth class in blinkpy."""

    def setUp(self):
        """Set up Login Handler."""
        self.auth = Auth()

    def tearDown(self):
        """Clean up after test."""
        self.auth = None

    @mock.patch("blinkpy.helpers.util.gen_uid")
    @mock.patch("blinkpy.auth.util.getpass")
    def test_empty_init(self, getpwd, genuid):
        """Test initialization with no params."""
        auth = Auth()
        self.assertDictEqual(auth.data, {})
        getpwd.return_value = "bar"
        genuid.return_value = 1234
        with mock.patch("builtins.input", return_value="foo"):
            auth.validate_login()
        expected_data = {
            "username": "foo",
            "password": "bar",
            "uid": 1234,
            "notification_key": 1234,
            "device_id": const.DEVICE_ID,
        }
        self.assertDictEqual(auth.data, expected_data)

    @mock.patch("blinkpy.helpers.util.gen_uid")
    @mock.patch("blinkpy.auth.util.getpass")
    def test_barebones_init(self, getpwd, genuid):
        """Test basebones initialization."""
        login_data = {"username": "foo", "password": "bar"}
        auth = Auth(login_data)
        self.assertDictEqual(auth.data, login_data)
        getpwd.return_value = "bar"
        genuid.return_value = 1234
        with mock.patch("builtins.input", return_value="foo"):
            auth.validate_login()
        expected_data = {
            "username": "foo",
            "password": "bar",
            "uid": 1234,
            "notification_key": 1234,
            "device_id": const.DEVICE_ID,
        }
        self.assertDictEqual(auth.data, expected_data)

    def test_full_init(self):
        """Test full initialization."""
        login_data = {
            "username": "foo",
            "password": "bar",
            "token": "token",
            "host": "host",
            "region_id": "region_id",
            "client_id": "client_id",
            "account_id": "account_id",
            "uid": 1234,
            "notification_key": 4321,
            "device_id": "device_id",
        }
        auth = Auth(login_data)
        self.assertEqual(auth.token, "token")
        self.assertEqual(auth.host, "host")
        self.assertEqual(auth.region_id, "region_id")
        self.assertEqual(auth.client_id, "client_id")
        self.assertEqual(auth.account_id, "account_id")
        auth.validate_login()
        self.assertDictEqual(auth.login_attributes, login_data)

    def test_bad_response_code(self):
        """Check bad response code from server."""
        self.auth.is_errored = False
        fake_resp = mresp.MockResponse({"code": 404}, 404)
        with self.assertRaises(exceptions.ConnectionError):
            self.auth.validate_response(fake_resp, True)
        self.assertTrue(self.auth.is_errored)

        self.auth.is_errored = False
        fake_resp = mresp.MockResponse({"code": 101}, 401)
        with self.assertRaises(UnauthorizedError):
            self.auth.validate_response(fake_resp, True)
        self.assertTrue(self.auth.is_errored)

    def test_good_response_code(self):
        """Check good response code from server."""
        fake_resp = mresp.MockResponse({"foo": "bar"}, 200)
        self.auth.is_errored = True
        self.assertEqual(self.auth.validate_response(fake_resp, True), {"foo": "bar"})
        self.assertFalse(self.auth.is_errored)

    def test_response_not_json(self):
        """Check response when not json."""
        fake_resp = "foobar"
        self.auth.is_errored = True
        self.assertEqual(self.auth.validate_response(fake_resp, False), "foobar")
        self.assertFalse(self.auth.is_errored)

    def test_response_bad_json(self):
        """Check response when not json but expecting json."""
        self.auth.is_errored = False
        with self.assertRaises(BlinkBadResponse):
            self.auth.validate_response(None, True)
        self.assertTrue(self.auth.is_errored)

    def test_header(self):
        """Test header data."""
        self.auth.token = "bar"
        expected_header = {"TOKEN_AUTH": "bar", "user-agent": const.DEFAULT_USER_AGENT}
        self.assertDictEqual(self.auth.header, expected_header)

    def test_header_no_token(self):
        """Test header without token."""
        self.auth.token = None
        self.assertEqual(self.auth.header, None)

    @mock.patch("blinkpy.auth.Auth.validate_login", return_value=None)
    @mock.patch("blinkpy.auth.api.request_login")
    def test_login(self, mock_req, mock_validate):
        """Test login handling."""
        fake_resp = mresp.MockResponse({"foo": "bar"}, 200)
        mock_req.return_value = fake_resp
        self.assertEqual(self.auth.login(), {"foo": "bar"})

    @mock.patch("blinkpy.auth.Auth.validate_login", return_value=None)
    @mock.patch("blinkpy.auth.api.request_login")
    def test_login_bad_response(self, mock_req, mock_validate):
        """Test login handling when bad response."""
        fake_resp = mresp.MockResponse({"foo": "bar"}, 404)
        mock_req.return_value = fake_resp
        self.auth.is_errored = False
        with self.assertRaises(LoginError):
            self.auth.login()
        with self.assertRaises(TokenRefreshFailed):
            self.auth.refresh_token()
        self.assertTrue(self.auth.is_errored)

    @mock.patch("blinkpy.auth.Auth.login")
    def test_refresh_token(self, mock_login):
        """Test refresh token method."""
        mock_login.return_value = {
            "region": {"tier": "test"},
            "authtoken": {"authtoken": "foobar"},
            "client": {"id": 1234},
            "account": {"id": 5678},
        }
        self.assertTrue(self.auth.refresh_token())
        self.assertEqual(self.auth.region_id, "test")
        self.assertEqual(self.auth.token, "foobar")
        self.assertEqual(self.auth.client_id, 1234)
        self.assertEqual(self.auth.account_id, 5678)

    @mock.patch("blinkpy.auth.Auth.login")
    def test_refresh_token_failed(self, mock_login):
        """Test refresh token failed."""
        mock_login.return_value = {}
        self.auth.is_errored = False
        with self.assertRaises(TokenRefreshFailed):
            self.auth.refresh_token()
        self.assertTrue(self.auth.is_errored)

    def test_check_key_required(self):
        """Check key required method."""
        self.auth.login_response = {}
        self.assertFalse(self.auth.check_key_required())

        self.auth.login_response = {"client": {"verification_required": False}}
        self.assertFalse(self.auth.check_key_required())

        self.auth.login_response = {"client": {"verification_required": True}}
        self.assertTrue(self.auth.check_key_required())

    @mock.patch("blinkpy.auth.api.request_verify")
    def test_send_auth_key(self, mock_req):
        """Check sending of auth key."""
        mock_blink = MockBlink(None)
        mock_req.return_value = mresp.MockResponse({"valid": True}, 200)
        self.assertTrue(self.auth.send_auth_key(mock_blink, 1234))
        self.assertTrue(mock_blink.available)

        mock_req.return_value = mresp.MockResponse(None, 200)
        self.assertFalse(self.auth.send_auth_key(mock_blink, 1234))

        mock_req.return_value = mresp.MockResponse({}, 200)
        self.assertFalse(self.auth.send_auth_key(mock_blink, 1234))

        self.assertTrue(self.auth.send_auth_key(mock_blink, None))

    @mock.patch("blinkpy.auth.api.request_verify")
    def test_send_auth_key_fail(self, mock_req):
        """Check handling of auth key failure."""
        mock_blink = MockBlink(None)
        mock_req.return_value = mresp.MockResponse(None, 200)
        self.assertFalse(self.auth.send_auth_key(mock_blink, 1234))
        mock_req.return_value = mresp.MockResponse({}, 200)
        self.assertFalse(self.auth.send_auth_key(mock_blink, 1234))

    @mock.patch("blinkpy.auth.Auth.validate_response")
    @mock.patch("blinkpy.auth.Auth.refresh_token")
    def test_query_retry(self, mock_refresh, mock_validate):
        """Check handling of request retry."""
        self.auth.session = MockSession()
        mock_validate.side_effect = [UnauthorizedError, "foobar"]
        mock_refresh.return_value = True
        self.assertEqual(self.auth.query(url="http://example.com"), "foobar")

    @mock.patch("blinkpy.auth.Auth.validate_response")
    @mock.patch("blinkpy.auth.Auth.refresh_token")
    def test_query_retry_failed(self, mock_refresh, mock_validate):
        """Check handling of failed retry request."""
        self.auth.session = MockSession()
        mock_validate.side_effect = [UnauthorizedError, BlinkBadResponse]
        mock_refresh.return_value = True
        self.assertEqual(self.auth.query(url="http://example.com"), None)

        mock_validate.side_effect = [UnauthorizedError, TokenRefreshFailed]
        self.assertEqual(self.auth.query(url="http://example.com"), None)

    def test_default_session(self):
        """Test default session creation."""
        sess = self.auth.create_session()
        adapter = sess.adapters["https://"]
        self.assertEqual(adapter.max_retries.total, 3)
        self.assertEqual(adapter.max_retries.backoff_factor, 1)
        self.assertEqual(
            adapter.max_retries.status_forcelist, [429, 500, 502, 503, 504]
        )

    def test_custom_session_full(self):
        """Test full custom session creation."""
        opts = {"backoff": 2, "retries": 10, "retry_list": [404]}
        sess = self.auth.create_session(opts=opts)
        adapter = sess.adapters["https://"]
        self.assertEqual(adapter.max_retries.total, 10)
        self.assertEqual(adapter.max_retries.backoff_factor, 2)
        self.assertEqual(adapter.max_retries.status_forcelist, [404])

    def test_custom_session_partial(self):
        """Test partial custom session creation."""
        opts1 = {"backoff": 2}
        opts2 = {"retries": 5}
        opts3 = {"retry_list": [101, 202]}
        sess1 = self.auth.create_session(opts=opts1)
        sess2 = self.auth.create_session(opts=opts2)
        sess3 = self.auth.create_session(opts=opts3)
        adapt1 = sess1.adapters["https://"]
        adapt2 = sess2.adapters["https://"]
        adapt3 = sess3.adapters["https://"]

        self.assertEqual(adapt1.max_retries.total, 3)
        self.assertEqual(adapt1.max_retries.backoff_factor, 2)
        self.assertEqual(adapt1.max_retries.status_forcelist, [429, 500, 502, 503, 504])

        self.assertEqual(adapt2.max_retries.total, 5)
        self.assertEqual(adapt2.max_retries.backoff_factor, 1)
        self.assertEqual(adapt2.max_retries.status_forcelist, [429, 500, 502, 503, 504])

        self.assertEqual(adapt3.max_retries.total, 3)
        self.assertEqual(adapt3.max_retries.backoff_factor, 1)
        self.assertEqual(adapt3.max_retries.status_forcelist, [101, 202])


class MockSession:
    """Object to mock a session."""

    def send(self, *args, **kwargs):
        """Mock send function."""
        return None


class MockBlink:
    """Object to mock basic blink class."""

    def __init__(self, login_response):
        """Initialize mock blink class."""
        self.available = False
        self.login_response = login_response
