"""Login handler for blink."""
import logging
from functools import partial
from requests import Request, Session, exceptions
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from blinkpy import api
from blinkpy.helpers import util
from blinkpy.helpers.constants import (
    BLINK_URL,
    DEFAULT_USER_AGENT,
    LOGIN_ENDPOINT,
    TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)


class Auth:
    """Class to handle login communication."""

    def __init__(self, login_data=None, no_prompt=False):
        """
        Initialize auth handler.

        :param login_data: dictionary for login data
                           must contain the following:
                             - username
                             - password
        :param no_prompt: Should any user input prompts
                          be supressed? True/FALSE
        """
        if login_data is None:
            login_data = {}
        self.data = login_data
        self.token = login_data.get("token", None)
        self.host = login_data.get("host", None)
        self.region_id = login_data.get("region_id", None)
        self.client_id = login_data.get("client_id", None)
        self.account_id = login_data.get("account_id", None)
        self.login_response = None
        self.is_errored = False
        self.no_prompt = no_prompt
        self.session = self.create_session()

    @property
    def login_attributes(self):
        """Return a dictionary of login attributes."""
        self.data["token"] = self.token
        self.data["host"] = self.host
        self.data["region_id"] = self.region_id
        self.data["client_id"] = self.client_id
        self.data["account_id"] = self.account_id
        return self.data

    @property
    def header(self):
        """Return authorization header."""
        if self.token is None:
            return None
        return {
            "TOKEN_AUTH": self.token,
            "user-agent": DEFAULT_USER_AGENT,
            "content-type": "application/json",
        }

    def create_session(self, opts=None):
        """Create a session for blink communication."""
        if opts is None:
            opts = {}
        backoff = opts.get("backoff", 1)
        retries = opts.get("retries", 3)
        retry_list = opts.get("retry_list", [429, 500, 502, 503, 504])
        sess = Session()
        assert_status_hook = [
            lambda response, *args, **kwargs: response.raise_for_status()
        ]
        sess.hooks["response"] = assert_status_hook
        retry = Retry(
            total=retries, backoff_factor=backoff, status_forcelist=retry_list
        )
        adapter = HTTPAdapter(max_retries=retry)
        sess.mount("https://", adapter)
        sess.mount("http://", adapter)
        sess.get = partial(sess.get, timeout=TIMEOUT)
        return sess

    def prepare_request(self, url, headers, data, reqtype):
        """Prepare a request."""
        req = Request(reqtype.upper(), url, headers=headers, data=data)
        return req.prepare()

    def validate_login(self):
        """Check login information and prompt if not available."""
        self.data["username"] = self.data.get("username", None)
        self.data["password"] = self.data.get("password", None)
        if not self.no_prompt:
            self.data = util.prompt_login_data(self.data)

        self.data = util.validate_login_data(self.data)

    def login(self, login_url=LOGIN_ENDPOINT):
        """Attempt login to blink servers."""
        self.validate_login()
        _LOGGER.info("Attempting login with %s", login_url)
        response = api.request_login(
            self,
            login_url,
            self.data,
            is_retry=False,
        )
        try:
            if response.status_code == 200:
                return response.json()
            raise LoginError
        except AttributeError as error:
            raise LoginError from error

    def logout(self, blink):
        """Log out."""
        return api.request_logout(blink)

    def refresh_token(self):
        """Refresh auth token."""
        self.is_errored = True
        try:
            _LOGGER.info("Token expired, attempting automatic refresh.")
            self.login_response = self.login()
            self.extract_login_info()
            self.is_errored = False
        except LoginError as error:
            _LOGGER.error("Login endpoint failed. Try again later.")
            raise TokenRefreshFailed from error
        except (TypeError, KeyError) as error:
            _LOGGER.error("Malformed login response: %s", self.login_response)
            raise TokenRefreshFailed from error
        return True

    def extract_login_info(self):
        """Extract login info from login response."""
        self.region_id = self.login_response["account"]["tier"]
        self.host = f"{self.region_id}.{BLINK_URL}"
        self.token = self.login_response["auth"]["token"]
        self.client_id = self.login_response["account"]["client_id"]
        self.account_id = self.login_response["account"]["account_id"]

    def startup(self):
        """Initialize tokens for communication."""
        self.validate_login()
        if None in self.login_attributes.values():
            self.refresh_token()

    def validate_response(self, response, json_resp):
        """Check for valid response."""
        if not json_resp:
            self.is_errored = False
            return response
        self.is_errored = True
        try:
            if response.status_code in [101, 401]:
                raise UnauthorizedError
            if response.status_code == 404:
                raise exceptions.ConnectionError
            json_data = response.json()
        except KeyError:
            pass
        except (AttributeError, ValueError) as error:
            raise BlinkBadResponse from error

        self.is_errored = False
        return json_data

    def query(
        self,
        url=None,
        data=None,
        headers=None,
        reqtype="get",
        stream=False,
        json_resp=True,
        is_retry=False,
        timeout=TIMEOUT,
    ):
        """
        Perform server requests.

        :param url: URL to perform request
        :param data: Data to send
        :param headers: Headers to send
        :param reqtype: Can be 'get' or 'post' (default: 'get')
        :param stream: Stream response? True/FALSE
        :param json_resp: Return JSON response? TRUE/False
        :param is_retry: Is this part of a re-auth attempt? True/FALSE
        """
        req = self.prepare_request(url, headers, data, reqtype)
        try:
            response = self.session.send(req, stream=stream, timeout=timeout)
            return self.validate_response(response, json_resp)
        except (exceptions.ConnectionError, exceptions.Timeout):
            _LOGGER.error(
                "Connection error. Endpoint %s possibly down or throttled.",
                url,
            )
        except BlinkBadResponse:
            code = None
            reason = None
            try:
                code = response.status_code
                reason = response.reason
            except AttributeError:
                pass
            _LOGGER.error(
                "Expected json response from %s, but received: %s: %s",
                url,
                code,
                reason,
            )
        except UnauthorizedError:
            try:
                if not is_retry:
                    self.refresh_token()
                    return self.query(
                        url=url,
                        data=data,
                        headers=self.header,
                        reqtype=reqtype,
                        stream=stream,
                        json_resp=json_resp,
                        is_retry=True,
                        timeout=timeout,
                    )
                _LOGGER.error("Unable to access %s after token refresh.", url)
            except TokenRefreshFailed:
                _LOGGER.error("Unable to refresh token.")
        return None

    def send_auth_key(self, blink, key):
        """Send 2FA key to blink servers."""
        if key is not None:
            response = api.request_verify(self, blink, key)
            try:
                json_resp = response.json()
                blink.available = json_resp["valid"]
                if not json_resp["valid"]:
                    _LOGGER.error("%s", json_resp["message"])
                    return False
            except (KeyError, TypeError):
                _LOGGER.error("Did not receive valid response from server.")
                return False
        return True

    def check_key_required(self):
        """Check if 2FA key is required."""
        try:
            if self.login_response["account"]["client_verification_required"]:
                return True
        except (KeyError, TypeError):
            pass
        return False


class TokenRefreshFailed(Exception):
    """Class to throw failed refresh exception."""


class LoginError(Exception):
    """Class to throw failed login exception."""


class BlinkBadResponse(Exception):
    """Class to throw bad json response exception."""


class UnauthorizedError(Exception):
    """Class to throw an unauthorized access error."""
