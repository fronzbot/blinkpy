"""Simple mock responses definitions."""

from blinkpy.blinkpy import BlinkURLHandler
import blinkpy.helpers.constants as const

LOGIN_RESPONSE = {
    'region': {'mock': 'Test'},
    'networks': {
        'summary': {'name': 'TestNetwork'},
        'networks': [{
            'name': 'TestNetwork',
            'account_id': 1111,
            'id': 2222,
            'armed': True,
            'arm_string': 'Armed'
        }]
    },
    'authtoken': {'authtoken': 'foobar123', 'message': 'auth'}
}


def mocked_requests_post(*args, **kwargs):
    """Mock post request."""
    class MockPostResponse:
        """Class for mock post response."""

        def __init__(self, json_data, status_code):
            """Initialize mock post response."""
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            """Return json data from post request."""
            return self.json_data

    url_arg = args[0]

    response_to_return = {'message': 'Error', 'code': 404}
    code_to_return = 404

    if url_arg == const.LOGIN_URL or url_arg == const.LOGIN_BACKUP_URL:
        response_to_return = LOGIN_RESPONSE
        code_to_return = 200
    elif url_arg is not None:
        response_to_return = {'message': 'foobar', 'code': 200}
        code_to_return = 200

    return MockPostResponse(response_to_return, code_to_return)


def mocked_requests_get(*args, **kwargs):
    """Mock get request."""
    class MockGetResponse:
        """Class for mock get response."""

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

    rx_header = kwargs.pop('headers')
    expected_token = LOGIN_RESPONSE['authtoken']['authtoken']
    if ('Content-Type' not in rx_header
            and rx_header['TOKEN_AUTH'] != expected_token):
        return MockGetResponse({'message': 'Not Authorized', 'code': 400}, 400)

    url_arg = args[0]

    if url_arg == 'use_bad_response':
        return MockGetResponse({'foo': 'bar'}, 200)
    elif url_arg == 'reauth':
        return MockGetResponse({'message': 'REAUTH', 'code': 777}, 777)

    return MockGetResponse({'test': 'foo'}, 200)


class MockURLHandler(BlinkURLHandler):
    """Mocks URL Handler in blinkpy module."""

    pass
