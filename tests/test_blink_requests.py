import blinkpy
import requests
import unittest
from unittest import mock
from blinkpy import LOGIN_URL
from blinkpy import BASE_URL
from blinkpy import HOST_URL

def mocked_requests_post(*args, **kwargs):
    class MockPostResponse:
        def __init__(self,json_data,status_code):
            self.json_data = json_data
            self.status_code = status_code
        def json(self):
            return self.json_data
            
    if args[0] == LOGIN_URL:
        return MockPostResponse({"authtoken":{"authtoken":"abcd1234"}}, 200)
    elif args[0].split("/")[-1] == 'arm':
        return MockPostResponse({"armed":True}, 200)
    elif args[0].split("/")[-1] == 'disarm':
        return MockPostResponse({"armed":False}, 200)
    else:
        return MockPostResponse({}, 200)
    
    return MockPostResponse({'message':'ERROR','code':404}, 404)
    
def mocked_requests_get(*args, **kwargs):
    class MockGetResponse:
        def __init__(self,json_data,status_code):
            self.json_data = json_data
            self.status_code = status_code
        def json(self):
            return self.json_data
            
    if args[0] == BASE_URL + '/networks':
        return MockGetResponse({'networks':[{"id":7777,"account_id":3333},{"nothing":"nothing"}]}, 200)
    else:
        return MockGetResponse({'devices':[{'device_type':'camera','name':'test','device_id':123,'armed':False,'thumbnail':'/some/url','temp':65,'battery':3,'notifications':1},
                                           {'device_type':'camera','name':'test2','device_id':321,'armed':True,'thumbnail':'/some/new/url','temp':56,'battery':5,'notifications':0},
                                           {'device_type':'None'}
                                           ],
                                'events':[{'camera_id':123, 'type':'motion', 'video_url':'/some/dumb/location.mp4'},
                                          {'camera_id':321, 'type':'None'}
                                          ],
                                'syncmodule':{'name':'SyncName', 'status':'online'},
                                'network':{'name':'Sync','armed':True, 'notifications':4}
                                }, 
                                200
                               )
                               
    
    return MockGetResponse({'message':'ERROR','code':404}, 404)
    
class TestBlinkRequests(unittest.TestCase):
    @mock.patch('blinkpy.requests.post', side_effect=mocked_requests_post)
    @mock.patch('blinkpy.requests.get', side_effect=mocked_requests_get)
    def test_blink_setup(self, mock_get, mock_post):
        blink = blinkpy.Blink(username='user',password='password')
        blink.setup_system()
        
        self.assertEqual(blink.network_id, '7777')
        self.assertEqual(blink.account_id, '3333')
        self.assertEqual(blink.online, True)
        self.assertEqual(blink.arm, True)
    
    @mock.patch('blinkpy.requests.post', side_effect=mocked_requests_post)
    @mock.patch('blinkpy.requests.get', side_effect=mocked_requests_get)
    def test_blink_camera_setup_and_motion(self, mock_get, mock_post):
        blink = blinkpy.Blink(username='user',password='password')
        blink.setup_system()
        blink.last_motion()
        for camera in blink.cameras:
            if camera.id == 123:
                assert camera.name is 'test'
                assert camera.armed is False
                assert camera.motion['video'] is BASE_URL+'/some/dumb/location.mp4'
            elif camera.id == 321:
                assert camera.name is 'test2'
                assert camera.armed is True
                assert len(camera.motion.keys()) is 0
        