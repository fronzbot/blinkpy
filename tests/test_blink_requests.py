import blinkpy
import requests
import unittest
from unittest import mock
from blinkpy import LOGIN_URL
from blinkpy import BASE_URL
import test_const as const

def mocked_requests_post(*args, **kwargs):
    class MockPostResponse:
        def __init__(self,json_data,status_code):
            self.json_data = json_data
            self.status_code = status_code
        def json(self):
            return self.json_data
            
    if args[0] == LOGIN_URL:
        return MockPostResponse({"region":{const.REGION_ID: const.REGION}, "authtoken":{"authtoken":const.TOKEN}}, 200)
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
        return MockGetResponse({'networks':[{"id":const.NETWORK_ID,"account_id":const.ACCOUNT_ID},{"nothing":"nothing"}]}, 200)
    else:
        return MockGetResponse(const.response, 200)
                               
    
    return MockGetResponse({'message':'ERROR','code':404}, 404)
    
class TestBlinkRequests(unittest.TestCase):
    @mock.patch('blinkpy.requests.post', side_effect=mocked_requests_post)
    @mock.patch('blinkpy.requests.get', side_effect=mocked_requests_get)
    def test_blink_setup(self, mock_get, mock_post):
        blink = blinkpy.Blink(username='user',password='password')
        blink.setup_system()
        
        self.assertEqual(blink.network_id, str(const.NETWORK_ID))
        self.assertEqual(blink.account_id, str(const.ACCOUNT_ID))
        self.assertEqual(blink.region, const.REGION)
        self.assertEqual(blink.region_id, const.REGION_ID)
        self.assertEqual(blink.online, const.ISONLINE)
        self.assertEqual(blink.arm, const.ARMED)
    
    @mock.patch('blinkpy.requests.post', side_effect=mocked_requests_post)
    @mock.patch('blinkpy.requests.get', side_effect=mocked_requests_get)
    def test_blink_camera_setup_and_motion(self, mock_get, mock_post):
        blink = blinkpy.Blink(username='user',password='password')
        blink.setup_system()
        blink.last_motion()
        for name, camera in blink.cameras.items():
            if camera.id == str(const.DEVICE_ID):
                 self.assertEqual(name, const.CAMERA_NAME)
                 self.assertEqual(camera.armed, const.ARMED)
                 self.assertEqual(camera.motion['video'], BASE_URL + const.THUMB + '.mp4')
                 self.assertEqual(camera.header, const.auth_header)
            elif camera.id == str(const.DEVICE_ID2):
                 self.assertEqual(name, const.CAMERA_NAME2)
                 self.assertEqual(camera.armed, const.ARMED2)
                 self.assertEqual(len(camera.motion.keys()), 0)
            else:
                assert False is True
                
    @mock.patch('blinkpy.requests.post', side_effect=mocked_requests_post)
    @mock.patch('blinkpy.requests.get', side_effect=mocked_requests_get)
    def test_blink_refresh(self, mock_get, mock_post):
        blink = blinkpy.Blink(username='user',password='password')
        blink.setup_system()
        const.response['devices'][0]['thumbnail'] = const.THUMB + const.THUMB2
        blink.refresh()
        for name, camera in blink.cameras.items():
            if camera.id == str(const.DEVICE_ID):
                self.assertEqual(camera.thumbnail, BASE_URL + const.THUMB + const.THUMB2 + '.jpg')
            elif camera.id == str(const.DEVICE_ID2):
                pass
            else:
                assert False is True
        
        const.response['devices'][0]['thumbnail'] = 'new'
        blink.cameras[const.CAMERA_NAME].image_refresh()
        for name, camera in blink.cameras.items():
            if camera.id == str(const.DEVICE_ID):
                self.assertEqual(camera.thumbnail, BASE_URL + 'new' + '.jpg')
            elif camera.id == str(const.DEVICE_ID2):
                pass
            else:
                assert False is True
        