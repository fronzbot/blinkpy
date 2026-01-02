"""Login handler for blink."""

import time
import uuid
import logging
from aiohttp import (
    ClientSession,
    ClientConnectionError,
    ContentTypeError,
    ClientResponse,
)
from blinkpy import api
from blinkpy.helpers import util
from blinkpy.helpers.pkce import generate_pkce_pair
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

        # OAuth v2 attributes
        self.hardware_id = login_data.get("hardware_id")
        if not self.hardware_id:
            self.hardware_id = str(uuid.uuid4()).upper()

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
        self.data["hardware_id"] = self.hardware_id
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

        if self.refresh_token and self.hardware_id:
            _LOGGER.debug("Attempting OAuth v2 token refresh")
            try:
                token_data = await api.oauth_refresh_token(
                    self, self.refresh_token, self.hardware_id
                )
                if token_data:
                    await self._process_token_data(token_data)
                    _LOGGER.info("OAuth v2 token refresh successful")
                    return
            except Exception as error:
                _LOGGER.debug("OAuth v2 refresh failed: %s", error)

        _LOGGER.debug("Attempting OAuth v2 login flow")
        success = await self._oauth_login_flow()
        if success:
            _LOGGER.info("OAuth v2 login successful")
            return

        raise LoginError("OAuth v2 login failed")

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

    async def _oauth_login_flow(self):
        """
        Execute complete OAuth 2.0 login flow with PKCE.

        Returns:
            bool: True if successful

        """
        # Step 1: Generate PKCE
        code_verifier, code_challenge = generate_pkce_pair()

        # Step 2: Authorization request
        auth_success = await api.oauth_authorize_request(
            self, self.hardware_id, code_challenge
        )
        if not auth_success:
            _LOGGER.error("OAuth authorization request failed")
            return False

        # Step 3: Get CSRF token
        csrf_token = await api.oauth_get_signin_page(self)
        if not csrf_token:
            _LOGGER.error("Failed to get CSRF token")
            return False

        # Step 4: Login
        email = self.data.get("username")
        password = self.data.get("password")

        login_result = await api.oauth_signin(self, email, password, csrf_token)

        # Step 4b: Handle 2FA if needed
        if login_result == "2FA_REQUIRED":
            # Store CSRF token and verifier for later use
            self._oauth_csrf_token = csrf_token
            self._oauth_code_verifier = code_verifier
            # Raise exception to let the app handle 2FA prompt
            _LOGGER.info("Two-factor authentication required.")
            raise BlinkTwoFARequiredError
        elif login_result != "SUCCESS":
            _LOGGER.error("Login failed")
            return False

        # Step 5: Get authorization code
        code = await api.oauth_get_authorization_code(self)
        if not code:
            _LOGGER.error("Failed to get authorization code")
            return False

        # Step 6: Exchange code for token
        token_data = await api.oauth_exchange_code_for_token(
            self, code, code_verifier, self.hardware_id
        )

        if not token_data:
            _LOGGER.error("Failed to exchange code for token")
            return False

        # Process tokens
        await self._process_token_data(token_data)
        return True

    async def _process_token_data(self, token_data):
        """Process token response data."""
        self.token = token_data.get("access_token")
        self.refresh_token = token_data.get("refresh_token")

        # Set expiration
        expires_in = token_data.get("expires_in", 3600)
        self.expires_in = expires_in
        self.expiration_date = time.time() + expires_in

        # Get tier info if needed (for account_id, region_id, host)
        if not self.host or not self.region_id or not self.account_id:
            try:
                self.tier_info = await self.get_tier_info()
                self.extract_tier_info()
            except Exception as error:
                _LOGGER.warning("Failed to get tier info: %s", error)

    async def complete_2fa_login(self, twofa_code):
        """
        Complete OAuth v2 login after 2FA verification.

        Args:
            twofa_code: 2FA code from user

        Returns:
            bool: True if successful

        """
        # Check if we have stored OAuth state
        if not hasattr(self, "_oauth_csrf_token") or not hasattr(
            self, "_oauth_code_verifier"
        ):
            _LOGGER.error("No OAuth 2FA state found. Start login flow first.")
            return False

        csrf_token = self._oauth_csrf_token
        code_verifier = self._oauth_code_verifier

        # Verify 2FA
        if not await api.oauth_verify_2fa(self, csrf_token, twofa_code):
            _LOGGER.error("2FA verification failed")
            return False

        # Step 5: Get authorization code
        code = await api.oauth_get_authorization_code(self)
        if not code:
            _LOGGER.error("Failed to get authorization code after 2FA")
            return False

        # Step 6: Exchange code for token
        token_data = await api.oauth_exchange_code_for_token(
            self, code, code_verifier, self.hardware_id
        )

        if not token_data:
            _LOGGER.error("Failed to exchange code for token after 2FA")
            return False

        # Process tokens
        await self._process_token_data(token_data)

        # Clean up temporary state
        delattr(self, "_oauth_csrf_token")
        delattr(self, "_oauth_code_verifier")

        return True


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
