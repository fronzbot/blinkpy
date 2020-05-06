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
        self,
        username=None,
        password=None,
        cred_file=None,
        persist_key=None,
        device_id="Blinkpy",
    ):
        """
        Initialize login handler.

        :param username: Blink username
        :param password: Blink password
        :param cred_file: JSON formatted credential file.
        :param persist_key: File location of persistant key.
        :param device_id: Name of application to send at login.
        """
        self.login_url = None
        self.login_urls = const.LOGIN_URLS
        self.cred_file = cred_file
        self.persist_key = persist_key
        self.device_id = device_id
        self.data = {
            "username": username,
            "password": password,
            "uid": None,
            "notification_key": None,
        }

        self.check_keys()

    def check_keys(self):
        """Check if uid exists, if not create."""
        uid = util.gen_uid(const.SIZE_UID)
        notification_key = util.gen_uid(const.SIZE_NOTIFICATION_KEY)
        data = {"uid": uid, "notification_key": notification_key}
        if self.persist_key is None:
            return data
        if not isfile(self.persist_key):
            with open(self.persist_key, "w") as json_file:
                json.dump(data, json_file)
        else:
            with open(self.persist_key, "r") as json_file:
                data = json.load(json_file)
        return data

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
                device_id=self.device_id,
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
            except (KeyError, TypeError):
                _LOGGER.error("Did not receive valid response from server.")
                return False
        return True

    def check_key_required(self, blink):
        """Check if 2FA key is required."""
        try:
            if blink.login_response["client"]["verification_required"]:
                return True
        except KeyError:
            pass
        return False
