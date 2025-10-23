"""Login handler for blink."""

import time
import logging
from aiohttp import (
    ClientSession,
    ClientConnectionError,
    ContentTypeError,
    ClientResponse,
)
from blinkpy import api
from blinkpy.helpers import util
from blinkpy.helpers.constants import (
    BLINK_URL,
    APP_BUILD,
    DEFAULT_USER_AGENT,
    LOGIN_ENDPOINT,
    TIER_ENDPOINT,
    TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)


class Auth:
    """Class to handle login communication."""

    def __init__(
        self,
        login_data=None,
        no_prompt=False,
        session=None,
        agent=DEFAULT_USER_AGENT,
        app_build=APP_BUILD,
        callback=None,
    ):
        """
        Initialize auth handler.

        :param login_data: dictionary for login data
                           must contain the following:
                             - username
                             - password
        :param no_prompt: Should any user input prompts
                          be suppressed? True/FALSE
        """
        if login_data is None:
            login_data = {}
        self.data = login_data
        self.token = login_data.get("token", None)
        self.expires_in = login_data.get("expires_in", None)
        self.expiration_date = login_data.get("expiration_date", None)
        self.refresh_token = login_data.get("refresh_token", None)
        self.host = login_data.get("host", None)
        self.region_id = login_data.get("region_id", None)
        self.client_id = login_data.get("client_id", None)
        self.account_id = login_data.get("account_id", None)
        self.user_id = login_data.get("user_id", None)
        self.login_response = None
        self.tier_info = None
        self.is_errored = False
        self.no_prompt = no_prompt
        self._agent = agent
        self._app_build = app_build
        self.session = session if session else ClientSession()

        # Callback to notify on token refresh
        self.callback = callback

    @property
    def login_attributes(self):
        """Return a dictionary of login attributes."""
        self.data["token"] = self.token
        self.data["expires_in"] = self.expires_in
        self.data["expiration_date"] = self.expiration_date
        self.data["refresh_token"] = self.refresh_token
        self.data["host"] = self.host
        self.data["region_id"] = self.region_id
        self.data["client_id"] = self.client_id
        self.data["account_id"] = self.account_id
        self.data["user_id"] = self.user_id
        return self.data

    @property
    def header(self):
        """Return authorization header."""
        if self.token is None:
            return None
        return {
            # "APP-BUILD": self._app_build,
            "Authorization": f"Bearer {self.token}",
            # "User-Agent": self._agent,
            "Content-Type": "application/json",
        }

    def validate_login(self):
        """Check login information and prompt if not available."""
        self.data["username"] = self.data.get("username", None)
        self.data["password"] = self.data.get("password", None)
        if not self.no_prompt:
            self.data = util.prompt_login_data(self.data)
        self.data = util.validate_login_data(self.data)

    async def login(self, login_url=LOGIN_ENDPOINT, refresh=False):
        """Attempt OAuth login to blink servers."""
        self.validate_login()
        response = await api.request_login(
            self,
            login_url,
            self.data,
            is_refresh=refresh,
            is_retry=False,
        )
        try:
            if response.status == 200:
                return await response.json()
            if response.status == 401:
                _LOGGER.error(
                    "Unable to refresh token. "
                    "Invalid refresh token or invalid credentials."
                )
                raise UnauthorizedError
            if response.status == 412:
                raise BlinkTwoFARequiredError
            raise LoginError
        except AttributeError as error:
            raise LoginError from error

    async def get_tier_info(self, tier_url=TIER_ENDPOINT):
        """Get tier information."""
        return await api.request_tier(self, tier_url)

    def logout(self, blink):
        """Log out."""
        return api.request_logout(blink)

    async def refresh_tokens(self, refresh=False):
        """Create or refresh access token."""
        self.is_errored = True
        try:
            _LOGGER.info(
                f"{'Refreshing' if refresh else 'Obtaining'} authentication token."
            )
            self.login_response = await self.login(refresh=refresh)
            self.extract_login_info()

            if not refresh:
                self.tier_info = await self.get_tier_info()
                self.extract_tier_info()

            self.is_errored = False
        except BlinkTwoFARequiredError as error:
            _LOGGER.error("Two-factor authentication required. Waiting for otp.")
            raise BlinkTwoFARequiredError from error
        except LoginError as error:
            _LOGGER.error("Login endpoint failed. Try again later.")
            raise TokenRefreshFailed from error
        except (TypeError, KeyError) as error:
            _LOGGER.error("Malformed login response: %s", self.login_response)
            raise TokenRefreshFailed from error
        return True

    def extract_login_info(self):
        """Extract login info from login response."""
        self.token = self.login_response["access_token"]
        self.expires_in = self.login_response["expires_in"]
        self.expiration_date = time.time() + self.expires_in
        self.refresh_token = self.login_response["refresh_token"]

    def extract_tier_info(self):
        """Extract tier info from tier info response."""
        self.region_id = self.tier_info["tier"]
        self.host = f"{self.region_id}.{BLINK_URL}"
        self.account_id = self.tier_info["account_id"]

    async def startup(self):
        """Initialize tokens for communication."""
        self.validate_login()
        if None in self.login_attributes.values():
            await self.refresh_tokens()

    async def validate_response(self, response: ClientResponse, json_resp):
        """Check for valid response."""
        if not json_resp:
            self.is_errored = False
            return response
        self.is_errored = True
        try:
            if response.status in [101, 401]:
                raise UnauthorizedError
            if response.status == 404:
                raise ClientConnectionError
            json_data = await response.json()
        except (AttributeError, ValueError) as error:
            raise BlinkBadResponse from error
        except ContentTypeError as error:
            _LOGGER.warning("Got text for JSON response: %s", await response.text())
            raise BlinkBadResponse from error

        self.is_errored = False
        return json_data

    def need_refresh(self):
        """Check if token needs refresh."""
        if self.expiration_date is None:
            return self.refresh_token is not None

        return self.expiration_date - time.time() < 60

    async def query(
        self,
        url=None,
        data=None,
        headers=None,
        reqtype="get",
        stream=False,
        json_resp=True,
        is_retry=False,
        timeout=TIMEOUT,
        skip_refresh_check=False,
    ):
        """Perform server requests.

        :param url: URL to perform request
        :param data: Data to send
        :param headers: Headers to send
        :param reqtype: Can be 'get' or 'post' (default: 'get')
        :param stream: Stream response? True/FALSE
        :param json_resp: Return JSON response? TRUE/False
        :param is_retry: Is this part of a re-auth attempt? True/FALSE
        """
        try:
            if not skip_refresh_check and self.need_refresh():
                await self.refresh_tokens(refresh=True)

                if "Authorization" in headers:
                    # update the authorization header with the new token
                    headers["Authorization"] = f"Bearer {self.token}"

                if self.callback is not None:
                    self.callback()

            if reqtype == "get":
                response = await self.session.get(
                    url=url, data=data, headers=headers, timeout=timeout
                )
            else:
                response = await self.session.post(
                    url=url, data=data, headers=headers, timeout=timeout
                )
            return await self.validate_response(response, json_resp)
        except (ClientConnectionError, TimeoutError) as er:
            _LOGGER.error(
                "Connection error. Endpoint %s possibly down or throttled. Error: %s",
                url,
                er,
            )
        except BlinkBadResponse:
            code = None
            reason = None
            try:
                code = response.status
                reason = response.reason
            except AttributeError:
                pass
            _LOGGER.error(
                "Expected json response from %s, but received: %s: %s",
                url,
                code,
                reason,
            )
        return None


class TokenRefreshFailed(Exception):
    """Class to throw failed refresh exception."""


class LoginError(Exception):
    """Class to throw failed login exception."""


class BlinkBadResponse(Exception):
    """Class to throw bad json response exception."""


class BlinkTwoFARequiredError(Exception):
    """Class to throw two-factor authentication required exception."""


class UnauthorizedError(Exception):
    """Class to throw an unauthorized access error."""
