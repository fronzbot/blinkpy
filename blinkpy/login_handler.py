"""Login handler for blink."""
import json
import logging
from os.path import isfile
from getpass import getpass
from blinkpy import api
from blinkpy.helpers import util
from blinkpy.helpers import constants as const

_LOGGER = logging.getLogger(__name__)


class LoginHandler:
    """Class to handle login communication."""

    def __init__(
        self, username=None, password=None, cred_file=None,
    ):
        """
        Initialize login handler.

        :param username: Blink username
        :param password: Blink password
        :param cred_file: JSON formatted credential file.
        """
        self.login_url = None
        self.login_urls = const.LOGIN_URLS
        self.cred_file = cred_file
        self.data = {
            "username": username,
            "password": password,
            "uid": util.gen_uid(const.SIZE_UID),
            "notification_key": util.gen_uid(const.SIZE_NOTIFICATION_KEY),
        }

    def check_cred_file(self):
        """Check if credential file supplied and use if so."""
        if isfile(self.cred_file):
            try:
                with open(self.cred_file, "r") as json_file:
                    creds = json.load(json_file)
                self.data["username"] = creds["username"]
                self.data["password"] = creds["password"]

            except ValueError:
                _LOGGER.error(
                    "Improperly formatted json file %s.", self.cred_file, exc_info=True
                )
                return False

            except KeyError:
                _LOGGER.error("JSON file information incomplete %s.", exc_info=True)
                return False
            return True
        return False

    def check_login(self):
        """Check login information and prompt if not available."""
        if self.data["username"] is None:
            self.data["username"] = input("Username:")
        if self.data["password"] is None:
            self.data["password"] = getpass("Password:")

        if self.data["username"] and self.data["password"]:
            return True
        return False

    def validate_response(self, url, response):
        """Validate response from login endpoint."""
        try:
            if response.status_code != 200:
                return False
        except AttributeError:
            _LOGGER.error(
                "Response for %s did not return a status code. Deprecated endpoint?",
                url,
            )
            return False
        return True

    def login(self, blink):
        """Attempt login to blink servers."""
        if self.cred_file is not None:
            self.check_cred_file()
        if not self.check_login():
            _LOGGER.error("Cannot login with username %s", self.data["username"])
            return False

        for url in self.login_urls:
            _LOGGER.info("Attempting login with %s", url)
            response = api.request_login(
                blink,
                url,
                self.data["username"],
                self.data["password"],
                self.data["notification_key"],
                self.data["uid"],
                is_retry=False,
            )

            if self.validate_response(url, response):
                self.login_url = url
                return response.json()

        _LOGGER.error("Failed to login to Blink servers.  Last response: %s", response)
        return False

    def send_auth_key(self, blink, key):
        """Send 2FA key to blink servers."""
        if key is not None:
            response = api.request_verify(blink, key)
            try:
                json_resp = response.json()
                blink.available = json_resp["valid"]
            except KeyError:
                blink.available = False
                _LOGGER.error("Did not receive valid response from server.")
        _LOGGER.error("Invalid key. Got %s", key)

    def check_key_required(self, blink):
        """Check if 2FA key is required."""
        # No idea if this is the right end point. Placeholder for now.
        try:
            if blink.login_response["account"]["email_verification_required"]:
                blink.available = False
                return True
        except KeyError:
            pass
        blink.available = True
        return False
