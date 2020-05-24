"""Login handler for blink."""
import logging
from functools import partial
from requests import Request, Session, exceptions
from blinkpy import api
from blinkpy.helpers import util
from blinkpy.helpers.constants import BLINK_URL, LOGIN_ENDPOINT
from blinkpy.helpers import errors as ERROR

_LOGGER = logging.getLogger(__name__)


class Auth:
    """Class to handle login communication."""

    def __init__(self, login_data=None, no_prompt=False):
        """
        Initialize auth handler.

        :param login_data: dictionary for login data
                           can contain the following:
                             - username
                             - password
                             - device_id
                             - uid
                             - notification_key
        :param no_prompt: Should any user input prompts
                          be supressed? True/FALSE
        """
        self.data = login_data
        self.token = None
        self.host = None
        self.region_id = None
        self.login_response = None
        self.no_prompt = no_prompt
        self.session = self.create_session()
        self.validate_login()

    @property
    def login_attributes(self):
        """Return a dictionary of login attributes."""
        attributes = {
            "token": self.token,
            "host": self.host,
            "region_id": self.region_id,
        }
        return util.merge_dicts(attributes, self.data)

    @property
    def header(self):
        """Return authorization header."""
        if self.token is None:
            return None
        return {"Host": self.host, "TOKEN_AUTH": self.token}

    def create_session(self):
        """Create a session for blink communication."""
        sess = Session()
        sess.get = partial(sess.get, timeout=10)
        return sess

    def prepare_request(self, url, headers, data, reqtype):
        """Prepare a request."""
        req = Request(reqtype.upper(), url, headers=headers, data=data)
        return req.prepare()

    def validate_login(self):
        """Check login information and prompt if not available."""
        if "username" not in self.data:
            self.data["username"] = None
        if "password" not in self.data:
            self.data["password"] = None
        if not self.no_prompt:
            self.data = util.prompt_login_data(self.data)

        self.data = util.validate_login_data(self.data)

    def login(self, login_url=LOGIN_ENDPOINT):
        """Attempt login to blink servers."""
        _LOGGER.info("Attempting login with %s", login_url)
        response = api.request_login(self, login_url, self.data, is_retry=False,)
        try:
            if response.status_code == 200:
                return response.json()
            raise LoginError
        except AttributeError:
            raise LoginError

    def refresh_token(self):
        """Refresh auth token."""
        try:
            _LOGGER.info("Token expired, attempting automatic refresh.")
            self.login_response = self.login()
            region_ids = (*self.login_response["region"],)
            self.region_id = region_ids[0]
            self.host = f"{self.region_id}.{BLINK_URL}"
            self.token = self.login_response["authtoken"]["authtoken"]
        except KeyError:
            _LOGGER.error("Malformed login response: %s", self.login_response)
            raise TokenRefreshFailed
        return True

    def validate_response(self, response, json_resp):
        """Check for valid response."""
        if not json_resp:
            return response

        json_data = response.json()
        try:
            if json_data["code"] in ERROR.BLINK_ERRORS:
                raise exceptions.ConnectionError
        except KeyError:
            pass

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
    ):
        """
        Perform server requests.

        :param url: URL to perform request
        :param data: Data to send
        :param headers: Headers to send
        :param reqtype: Can be 'get' or 'post' (default: 'get')
        :param stream: Stream response? True/FALSE
        :param json_resp: Return JSON response? TRUE/False
        :param is_retry: Is this a retry attempt? True/FALSE
        """

        req = self.prepare_request(url, headers, data, reqtype)
        try:
            response = self.session.send(req, stream=stream)
            return self.validate_response(response, json_resp)

        except (exceptions.ConnectionError, exceptions.Timeout, TokenRefreshFailed):
            try:
                if not is_retry:
                    self.refresh_token()
                    return self.query(
                        url=url,
                        data=data,
                        headers=headers,
                        reqtype=reqtype,
                        stream=stream,
                        json_resp=json_resp,
                        is_retry=True,
                    )
            except (TokenRefreshFailed, LoginError):
                _LOGGER.error("Endpoint %s failed. Unable to refresh login tokens", url)
        _LOGGER.error("Endpoint %s failed", url)
        return None

    def send_auth_key(self, blink, key):
        """Send 2FA key to blink servers."""
        if key is not None:
            response = api.request_verify(self, blink, key)
            try:
                json_resp = response.json()
                blink.available = json_resp["valid"]
            except (KeyError, TypeError):
                _LOGGER.error("Did not receive valid response from server.")
                return False
        return True

    def check_key_required(self):
        """Check if 2FA key is required."""
        try:
            if self.login_response["client"]["verification_required"]:
                return True
        except KeyError:
            pass
        return False


class TokenRefreshFailed(Exception):
    """Class to throw failed refresh exception."""


class LoginError(Exception):
    """Class to throw failed login exception."""
