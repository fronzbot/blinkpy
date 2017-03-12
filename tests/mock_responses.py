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

NEW_THUMBNAIL = '/NEW/THUMBNAIL/YAY'

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

MOCK_BYTES = '\x00\x10JFIF\x00\x01'

IMAGE_TO_WRITE_URL = list()
IMAGE_TO_WRITE_URL.append('https://ciri.' + const.BLINK_URL +
                          FIRST_CAMERA['thumbnail'] + '.jpg')
IMAGE_TO_WRITE_URL.append('https://ciri.' + const.BLINK_URL +
                          SECOND_CAMERA['thumbnail'] + '.jpg')

FAKE_FILES = list()


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

    # pylint: disable=global-variable-not-assigned
    global RESPONSE
    # pylint: disable=global-variable-not-assigned
    global NETWORKS_RESPONSE

    if args[0] is not None:
        url_tail = args[0].split("/")[-1]
    else:
        return MockPostResponse({'message': 'ERROR', 'code': 404}, 404)

    if args[0] == const.LOGIN_URL:
        # Request to login
        return MockPostResponse(LOGIN_RESPONSE, 200)
    elif args[0] == const.LOGIN_BACKUP_URL:
        return MockPostResponse(LOGIN_RESPONSE, 200)
    elif url_tail == 'arm' or url_tail == 'disarm':
        # Request to arm/disarm system
        NETWORKS_RESPONSE['networks'][0]['armed'] = url_tail == 'arm'
        RESPONSE['network']['armed'] = url_tail == 'arm'
        return MockPostResponse({}, 200)
    elif url_tail == 'enable' or url_tail == 'disable':
        # Request to enable/disable motion detection per camera
        received_id = args[0].split("/")[-2]
        all_devices = list()
        for element in RESPONSE['devices']:
            all_devices.append(element)
            current_id = element['device_id']
            if str(current_id) == received_id:
                element['armed'] = url_tail == 'enable'
                element['enabled'] = url_tail == 'enable'
        RESPONSE['devices'] = all_devices
        return MockPostResponse({}, 200)
    elif url_tail == 'thumbnail':
        # Requesting a new image
        received_id = args[0].split("/")[-2]
        all_devices = list()
        for element in RESPONSE['devices']:
            all_devices.append(element)
            if str(element['device_id']) == received_id:
                element['thumbnail'] = NEW_THUMBNAIL
        RESPONSE['devices'] = all_devices
        return MockPostResponse({}, 200)

    return MockPostResponse({'message': 'ERROR', 'code': 404}, 404)


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
            """Return json data from get request."""
            return self.json_data

        @property
        def raw(self):
            """Return raw data from get request."""
            return self.raw_data

    # pylint: disable=unused-variable
    (region_id, region), = LOGIN_RESPONSE['region'].items()
    set_region_id = args[0].split('/')[2].split('.')[0]
    if set_region_id == 'rest':
        set_region_id = (set_region_id + '.' +
                         args[0].split('/')[2].split('.')[1])
        region_id = 'rest.piri'
    neturl = 'https://' + set_region_id + '.' + const.BLINK_URL + '/networks'
    if args[0] == neturl:
        return MockGetResponse(NETWORKS_RESPONSE, 200)
    elif set_region_id != region_id:
        raise ConnectionError('Received region id ' + region_id +
                              ' Expected ' + set_region_id)
    elif args[0] in IMAGE_TO_WRITE_URL:
        return MockGetResponse({}, 200, raw_data=MOCK_BYTES)
    else:
        return MockGetResponse(RESPONSE, 200)

    return MockGetResponse({'message': 'ERROR', 'code': 404}, 404)


def mocked_copyfileobj(*args, **kwargs):
    """Mock shutil.copyfileobj."""
    class MockCopyFileObj:
        """Class for mock copy file."""

        def __init__(self, src, dst):
            """Initialize copyfile mock."""
            self.src = src
            self.dst = dst
    # pylint: disable=global-variable-not-assigned
    global FAKE_FILES
    mockobj = MockCopyFileObj(args[0], args[1])
    FAKE_FILES.append(mockobj.src)
    return


def get_test_cameras(base_url):
    """Helper function to return cameras named in this file."""
    test_cameras = dict()
    for element in RESPONSE['devices']:
        if ('device_type' in element and
                element['device_type'] == 'camera'):
            test_cameras[element['name']] = {
                'device_id': str(element['device_id']),
                'armed': element['armed'],
                'thumbnail': (base_url +
                              element['thumbnail'] + '.jpg'),
                'temperature': element['temp'],
                'battery': element['battery'],
                'notifications': element['notifications']
            }
    return test_cameras


def get_test_id_table():
    """Helper function to return mock id table."""
    test_id_table = dict()
    for element in RESPONSE['devices']:
        if ('device_type' in element and
                element['device_type'] == 'camera'):
            test_id_table[str(element['device_id'])] = element['name']
    return test_id_table
