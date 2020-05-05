"""Simple mock responses definitions."""

from blinkpy.helpers.util import BlinkURLHandler
import blinkpy.helpers.constants as const

LOGIN_RESPONSE = {
    "region": {"mock": "Test"},
    "networks": {"1234": {"name": "test", "onboarded": True}},
    "authtoken": {"authtoken": "foobar123", "message": "auth"},
    "client": {"id": "5678"},
    "account": {"id": "1337"},
}


class MockResponse:
    """Class for mock request response."""

    def __init__(self, json_data, status_code, raw_data=None):
        """Initialize mock get response."""
        self.json_data = json_data
        self.status_code = status_code
        self.raw_data = raw_data

    def json(self):
        """Return json data from get_request."""
        return self.json_data

    @property
    def raw(self):
        """Return raw data from get request."""
        return self.raw_data


def mocked_session_send(*args, **kwargs):
    """Mock session."""
    prepped = args[0]
    url = prepped.url
    header = prepped.headers
    method = prepped.method
    if method == "GET":
        expected_token = LOGIN_RESPONSE["authtoken"]["authtoken"]
        if header["TOKEN_AUTH"] != expected_token:
            response = {"message": "Not Authorized", "code": 400}
            status = 400
        elif url == "use_bad_response":
            response = {"foo": "bar"}
            status = 200
        elif url == "reauth":
            response = {"message": "REAUTH", "code": 777}
            status = 777
        else:
            response = {"test": "foo"}
            status = 200
    elif method == "POST":
        if url in const.LOGIN_URLS:
            response = LOGIN_RESPONSE
            status = 200
        elif url == "http://wrong.url/" or url is None:
            response = {"message": "Error", "code": 404}
            status = 404
        else:
            response = {"message": "foo", "code": 200}
            status = 200

    return MockResponse(response, status)


class MockURLHandler(BlinkURLHandler):
    """Mocks URL Handler in blinkpy module."""
