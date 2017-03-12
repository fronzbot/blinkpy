"""
Mock responses that mimic actual responses from Blink servers.

This file should be updated any time the Blink server responses
change so we can make sure blinkpy can still communicate.
"""

import helpers.constants as const

NETWORKS_RESPONSE = {}
NETWORKS_RESPONSE['summary'] = {'onboarded': True, 'name': 'Nilfgaard'}
NETWORKS_RESPONSE['networks'] = [{
    'network_key': None,
    'name': NETWORKS_RESPONSE['summary']['name'],
    'account_id': 1989,
    'id': 9898,
    'encryption_key': None,
    'armed': True,
    'ping_interval': 60,
    'video_destination': 'server',
    'arm_string': 'Armed',
    'feature_plan_id': None
}]

FIRST_CAMERA = {'device_type': 'camera',
                'notifications': 1,
                'battery': 2,
                'active': 'enabled',
                'enabled': True,
                'temp': 70,
                'updated_at': '2017-01-01T01:23:45+00:00',
                'lfr_strength': 3,
                'armed': True,
                'device_id': 2112,
                'wifi_strength': 5,
                'thumbnail': '/this/is/url1/thumb',
                'name': 'First Camera',
                'status': 'done'}

SECOND_CAMERA = {'device_type': 'camera',
                 'notifications': 0,
                 'battery': 3,
                 'active': 'disabled',
                 'enabled': False,
                 'temp': 82,
                 'updated_at': '2017-12-21T01:21:12+00:00',
                 'lfr_strength': 1,
                 'armed': False,
                 'device_id': 1221,
                 'wifi_strength': 1,
                 'thumbnail': '/this/is/url2/thumb',
                 'name': 'Second Camera',
                 'status': 'done'}

SYNC_MODULE = {'updated_at': '1970-01-01T01:00:00+00:00',
               'device_type': 'sync_module',
               'notifications': 2,
               'device_id': 7990,
               'status': 'online'}

FIRST_EVENT = {'camera_name': FIRST_CAMERA['name'],
               'updated_at': '2017-10-10T03:37:37+00:00',
               'sync_module_id': None,
               'camera': FIRST_CAMERA['device_id'],
               'type': 'motion',
               'duration': None,
               'status': None,
               'created_at': '2017-01-28T19:51:52+00:00',
               'camera_id': FIRST_CAMERA['device_id'],
               'id': 666777888,
               'siren_id': None,
               'account_id': NETWORKS_RESPONSE['networks'][0]['account_id'],
               'notified': True,
               'siren': None,
               'syncmodule': None,
               'video_url': FIRST_CAMERA['thumbnail'] + '.mp4',
               'command_id': None,
               'network_id': None,
               'account': NETWORKS_RESPONSE['networks'][0]['account_id'],
               'video_id': 123000321}

SECOND_EVENT = {'updated_at': '2017-01-28T19:51:29+00:00',
                'sync_module_id': SYNC_MODULE['device_id'],
                'camera': None,
                'type': 'armed',
                'duration': None,
                'status': None,
                'created_at': '2017-01-28T19:51:29+00:00',
                'camera_id': None,
                'id': 333777555,
                'siren_id': None,
                'account_id': NETWORKS_RESPONSE['networks'][0]['account_id'],
                'notified': False,
                'siren': None,
                'syncmodule': SYNC_MODULE['device_id'],
                'command_id': None,
                'network_id': None,
                'account': NETWORKS_RESPONSE['networks'][0]['account_id']}

"""Fake response content."""
LOGIN_RESPONSE = {}
LOGIN_RESPONSE['region'] = {'ciri': 'Cintra'}
LOGIN_RESPONSE['networks'] = {
    NETWORKS_RESPONSE['networks'][0]['id']: NETWORKS_RESPONSE['summary']
}
LOGIN_RESPONSE['authtoken'] = {'authtoken': 'foobar7117', 'message': 'auth'}

RESPONSE = {}
RESPONSE['account'] = {'notifications': SYNC_MODULE['notifications']}
RESPONSE['devices'] = [FIRST_CAMERA, SECOND_CAMERA, SYNC_MODULE]
RESPONSE['network'] = {'armed': NETWORKS_RESPONSE['networks'][0]['armed'],
                       'wifi_strength': 4,
                       'warning': 0,
                       'name': NETWORKS_RESPONSE['summary']['name'],
                       'notifications': SYNC_MODULE['notifications']}
RESPONSE['event'] = [FIRST_EVENT, SECOND_EVENT]
RESPONSE['syncmodule'] = {'name': 'Vengerberg', 'status': 'online'}


def mocked_requests_post(*args, **kwargs):
    """Mock post request."""
    class MockPostResponse:
        """Class for mock post response."""

        def __init__(self, json_data, status_code):
            """Initialze mock post response."""
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            """Return json data from post request."""
            return self.json_data

    url_tail = args[0].split("/")[-1]
    if args[0] == const.LOGIN_URL:
        return MockPostResponse(LOGIN_RESPONSE, 200)
    elif url_tail == 'arm' or url_tail == 'disarm':
        # pylint: disable=global-variable-not-assigned
        global NETWORKS_RESPONSE
        # pylint: disable=global-variable-not-assigned
        global RESPONSE
        NETWORKS_RESPONSE['networks'][0]['armed'] = url_tail == 'arm'
        RESPONSE['network']['armed'] = url_tail == 'arm'
        return MockPostResponse({}, 200)

    return MockPostResponse({'message': 'ERROR', 'code': 404}, 404)


def mocked_requests_get(*args, **kwargs):
    """Mock get request."""
    class MockGetResponse:
        """Class for mock get response."""

        def __init__(self, json_data, status_code):
            """Initialze mock get response."""
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            """Return json data from post request."""
            return self.json_data
    # pylint: disable=unused-variable
    (region_id, region), = LOGIN_RESPONSE['region'].items()
    set_region_id = args[0].split('/')[2].split('.')[0]
    neturl = 'https://' + set_region_id + '.' + const.BLINK_URL + '/networks'
    if args[0] == neturl:
        return MockGetResponse(NETWORKS_RESPONSE, 200)
    elif set_region_id != region_id:
        raise ConnectionError('Received url ' + args[0])
    else:
        return MockGetResponse(RESPONSE, 200)

    return MockGetResponse({'message': 'ERROR', 'code': 404}, 404)
