"""Test login handler."""

from unittest import mock
from unittest import IsolatedAsyncioTestCase
from aiohttp import ClientConnectionError
from blinkpy.auth import (
    Auth,
    TokenRefreshFailed,
    BlinkBadResponse,
    UnauthorizedError,
)
import blinkpy.helpers.constants as const
import tests.mock_responses as mresp

USERNAME = "foobar"
PASSWORD = "deadbeef"


class TestAuth(IsolatedAsyncioTestCase):
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

    async def test_bad_response_code(self):
        """Check bad response code from server."""
        self.auth.is_errored = False
        fake_resp = mresp.MockResponse({"code": 404}, 404)
        with self.assertRaises(ClientConnectionError):
            await self.auth.validate_response(fake_resp, True)
        self.assertTrue(self.auth.is_errored)

        self.auth.is_errored = False
        fake_resp = mresp.MockResponse({"code": 101}, 401)
        with self.assertRaises(UnauthorizedError):
            await self.auth.validate_response(fake_resp, True)
        self.assertTrue(self.auth.is_errored)

    async def test_good_response_code(self):
        """Check good response code from server."""
        fake_resp = mresp.MockResponse({"foo": "bar"}, 200)
        self.auth.is_errored = True
        self.assertEqual(
            await self.auth.validate_response(fake_resp, True), {"foo": "bar"}
        )
        self.assertFalse(self.auth.is_errored)

    async def test_response_not_json(self):
        """Check response when not json."""
        fake_resp = "foobar"
        self.auth.is_errored = True
        self.assertEqual(await self.auth.validate_response(fake_resp, False), "foobar")
        self.assertFalse(self.auth.is_errored)

    async def test_response_bad_json(self):
        """Check response when not json but expecting json."""
        self.auth.is_errored = False
        with self.assertRaises(BlinkBadResponse):
            await self.auth.validate_response(None, True)
        self.assertTrue(self.auth.is_errored)

    def test_header(self):
        """Test header data."""
        self.auth.token = "bar"
        expected_header = {
            "TOKEN_AUTH": "bar",
            "user-agent": const.DEFAULT_USER_AGENT,
            "content-type": "application/json",
        }
        self.assertDictEqual(self.auth.header, expected_header)

    def test_header_no_token(self):
        """Test header without token."""
        self.auth.token = None
        self.assertEqual(self.auth.header, None)

    @mock.patch("blinkpy.auth.Auth.validate_login")
    @mock.patch("blinkpy.auth.Auth.refresh_token")
    async def test_auth_startup(self, mock_validate, mock_refresh):
        """Test auth startup."""
        await self.auth.startup()

    @mock.patch("blinkpy.auth.Auth.query")
    async def test_refresh_token(self, mock_resp):
        """Test refresh token method."""
        mock_resp.return_value.json = mock.AsyncMock(
            return_value={
                "account": {"account_id": 5678, "client_id": 1234, "tier": "test"},
                "auth": {"token": "foobar"},
            }
        )
        mock_resp.return_value.status = 200

        self.auth.no_prompt = True
        self.assertTrue(await self.auth.refresh_token())
        self.assertEqual(self.auth.region_id, "test")
        self.assertEqual(self.auth.token, "foobar")
        self.assertEqual(self.auth.client_id, 1234)
        self.assertEqual(self.auth.account_id, 5678)

        mock_resp.return_value.status = 400
        with self.assertRaises(TokenRefreshFailed):
            await self.auth.refresh_token()

        mock_resp.return_value.status = 200
        mock_resp.return_value.json = mock.AsyncMock(side_effect=AttributeError)
        with self.assertRaises(TokenRefreshFailed):
            await self.auth.refresh_token()

    @mock.patch("blinkpy.auth.Auth.login")
    async def test_refresh_token_failed(self, mock_login):
        """Test refresh token failed."""
        mock_login.return_value = {}
        self.auth.is_errored = False
        with self.assertRaises(TokenRefreshFailed):
            await self.auth.refresh_token()
        self.assertTrue(self.auth.is_errored)

    def test_check_key_required(self):
        """Check key required method."""
        self.auth.login_response = {}
        self.assertFalse(self.auth.check_key_required())

        self.auth.login_response = {"account": {"client_verification_required": False}}
        self.assertFalse(self.auth.check_key_required())

        self.auth.login_response = {"account": {"client_verification_required": True}}
        self.assertTrue(self.auth.check_key_required())

    @mock.patch("blinkpy.auth.api.request_logout")
    async def test_logout(self, mock_req):
        """Test logout method."""
        mock_blink = MockBlink(None)
        mock_req.return_value = True
        self.assertTrue(await self.auth.logout(mock_blink))

    @mock.patch("blinkpy.auth.api.request_verify")
    async def test_send_auth_key(self, mock_req):
        """Check sending of auth key."""
        mock_blink = MockBlink(None)
        mock_req.return_value = mresp.MockResponse({"valid": True}, 200)
        self.assertTrue(await self.auth.send_auth_key(mock_blink, 1234))
        self.assertTrue(mock_blink.available)

        mock_req.return_value = mresp.MockResponse(None, 200)
        self.assertFalse(await self.auth.send_auth_key(mock_blink, 1234))

        mock_req.return_value = mresp.MockResponse({}, 200)
        self.assertFalse(await self.auth.send_auth_key(mock_blink, 1234))

        self.assertTrue(await self.auth.send_auth_key(mock_blink, None))

    @mock.patch("blinkpy.auth.api.request_verify")
    async def test_send_auth_key_fail(self, mock_req):
        """Check handling of auth key failure."""
        mock_blink = MockBlink(None)
        mock_req.return_value = mresp.MockResponse(None, 200)
        self.assertFalse(await self.auth.send_auth_key(mock_blink, 1234))
        mock_req.return_value = mresp.MockResponse({}, 200)
        self.assertFalse(await self.auth.send_auth_key(mock_blink, 1234))
        mock_req.return_value = mresp.MockResponse(
            {"valid": False, "message": "Not good"}, 200
        )
        self.assertFalse(await self.auth.send_auth_key(mock_blink, 1234))

    @mock.patch(
        "blinkpy.auth.Auth.validate_response",
        mock.AsyncMock(side_effect=[UnauthorizedError, "foobar"]),
    )
    @mock.patch("blinkpy.auth.Auth.refresh_token", mock.AsyncMock(return_value=True))
    @mock.patch("blinkpy.auth.Auth.query", mock.AsyncMock(return_value="foobar"))
    async def test_query_retry(self):  # , mock_refresh, mock_validate):
        """Check handling of request retry."""
        self.auth.session = MockSession()
        self.assertEqual(await self.auth.query(url="http://example.com"), "foobar")

    @mock.patch("blinkpy.auth.Auth.validate_response")
    @mock.patch("blinkpy.auth.Auth.refresh_token")
    async def test_query_retry_failed(self, mock_refresh, mock_validate):
        """Check handling of failed retry request."""
        self.auth.session = MockSession()
        mock_validate.side_effect = [
            BlinkBadResponse,
            UnauthorizedError,
            TokenRefreshFailed,
        ]
        mock_refresh.return_value = True
        self.assertEqual(await self.auth.query(url="http://example.com"), None)
        self.assertEqual(await self.auth.query(url="http://example.com"), None)

    @mock.patch("blinkpy.auth.Auth.validate_response")
    async def test_query(self, mock_validate):
        """Test query functions."""
        self.auth.session = MockSession_with_data()
        await self.auth.query("URL", "data", "headers", "get")
        await self.auth.query("URL", "data", "headers", "post")

        mock_validate.side_effect = ClientConnectionError
        self.assertIsNone(await self.auth.query("URL", "data", "headers", "get"))

        mock_validate.side_effect = BlinkBadResponse
        self.assertIsNone(await self.auth.query("URL", "data", "headers", "post"))

        mock_validate.side_effect = UnauthorizedError
        self.auth.refresh_token = mock.AsyncMock()
        self.assertIsNone(await self.auth.query("URL", "data", "headers", "post"))


class MockSession:
    """Object to mock a session."""

    async def get(self, *args, **kwargs):
        """Mock send function."""
        return None

    async def post(self, *args, **kwargs):
        """Mock send function."""
        return None


class MockSession_with_data:
    """Object to mock a session."""

    async def get(self, *args, **kwargs):
        """Mock send function."""
        response = mock.AsyncMock
        response.status = 400
        response.reason = "Some Reason"
        return response

    async def post(self, *args, **kwargs):
        """Mock send function."""
        response = mock.AsyncMock
        response.status = 400
        response.reason = "Some Reason"
        return response


class MockBlink:
    """Object to mock basic blink class."""

    def __init__(self, login_response):
        """Initialize mock blink class."""
        self.available = False
        self.login_response = login_response
