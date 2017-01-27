ISONLINE = True
ARMED = True
ARMED2 = False
REGION_ID = 'test'
REGION = 'Oceaniaeurasia'
TOKEN = 'abcd1234$$@@'
NETWORK_ID = 1337
DEVICE_ID = 9876
DEVICE_ID2 = 6789
ACCOUNT_ID = 1234
CAMERA_NAME = 'My Camera'
CAMERA_NAME2 = 'Number 2'
BATTERY = 3
BATTERY2 = 1
TEMP = 70
TEMP2 = 66
THUMB = '/url/camera/7777/clip'
THUMB2 = '/url/camera/8888/clip'
NOTIFS = 1
NOTIFS2 = 1

if ISONLINE:
    ONLINE = 'online'
else:
    ONLINE = 'offline'
    

response = {'account': {'notifications': 1}, 
            'devices': [{'device_type': 'camera', 
                         'notifications': NOTIFS, 
                         'battery': BATTERY, 
                         'active': 'disabled', 
                         'errors': 0, 
                         'error_msg': '', 
                         'enabled': False, 
                         'temp': TEMP, 
                         'updated_at': '2017-01-27T03:14:24+00:00', 
                         'lfr_strength': 3, 
                         'armed': ARMED, 
                         'device_id': DEVICE_ID, 
                         'wifi_strength': 5, 
                         'warning': 0, 
                         'thumbnail': THUMB, 
                         'name': CAMERA_NAME, 
                         'status': 'done'},
                        {'device_type': 'camera', 
                         'notifications': NOTIFS2, 
                         'battery': BATTERY2, 
                         'active': 'disabled', 
                         'errors': 0, 
                         'error_msg': '', 
                         'enabled': False, 
                         'temp': TEMP2, 
                         'updated_at': '2017-01-27T03:14:24+00:00', 
                         'lfr_strength': 3, 
                         'armed': ARMED2, 
                         'device_id': DEVICE_ID2, 
                         'wifi_strength': 5, 
                         'warning': 0, 
                         'thumbnail': THUMB2, 
                         'name': CAMERA_NAME2, 
                         'status': 'done'}, 
                         {'updated_at': '2017-01-26T19:32:10+00:00', 
                         'device_type': 'sync_module', 
                         'notifications': 0, 
                         'device_id': 0000, 
                         'status': 
                         'online', 
                         'last_hb': 
                         '2017-01-27T03:14:49+00:00', 
                         'errors': 0, 
                         'error_msg': '', 
                         'warning': 0}], 
            'network': {'armed': ARMED, 
                        'wifi_strength': 5, 
                        'warning': 0, 
                        'error_msg': '', 
                        'name': 'Blink', 
                        'notifications': NOTIFS, 
                        'status': 'ok'},
            'events': [{'camera_id':DEVICE_ID, 
                        'type':'motion', 
                        'video_url':THUMB + '.mp4', 
                        'created_at':'2017-01-01'},
                       {'camera_id':DEVICE_ID2,
                        'type':'None'}],
            'syncmodule':{'name':'SyncName', 
                          'status':ONLINE}}
                        