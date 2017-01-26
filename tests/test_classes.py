import testtools
import unittest
import blinkpy
from blinkpy import BASE_URL

class TestBlink(unittest.TestCase):
    def test_blink_instance(self):
        blink = blinkpy.Blink()
        
    def test_blink_camera_attributes(self):
        config = {'name':'name', 'device_id': 1248, 'armed':True, 'thumbnail':'/test/url/image', 'temp':70, 'battery':3, 'notifications':0, 'region_id':'rid'}

        camera = blinkpy.BlinkCamera(config)
        
        # Check that values are properly stored and can be recalled
        self.assertEqual(camera.name, config['name'])
        self.assertEqual(camera.id, str(config['device_id']))
        self.assertEqual(camera.armed, config['armed'])
        self.assertEqual(camera.clip, BASE_URL + config['thumbnail'] + '.mp4')
        self.assertEqual(camera.thumbnail, BASE_URL + config['thumbnail'] + '.jpg')
        self.assertEqual(camera.temperature, config['temp'])
        self.assertEqual(camera.battery, config['battery'])
        self.assertEqual(camera.notifications, config['notifications'])
        self.assertEqual(camera.region_id, config['region_id'])
        
        # Check that values can be changed with individual methods
        test_header  = {'Header':'test','Test':'1234'}
        test_img     = 'http://image-link.com'
        test_arm     = 'http://arm-link.com'
        test_motion  = {'video':'url','image':'url','time':'timestamp'}
        
        camera.name  = config['name']+'_new'
        camera.clip  = BASE_URL + config['thumbnail'] + '.mp4_new'
        camera.thumbnail = BASE_URL + config['thumbnail'] + '.jpg_new'
        camera.temperature = config['temp'] + 10
        camera.battery = config['battery'] + 1
        camera.notifications = config['notifications'] + 1
        camera.image_link = test_img
        camera.arm_link = test_arm
        camera.header = test_header
        camera.motion = test_motion
        
        # Check that values are properly stored and can be recalled
        self.assertEqual(camera.name , config['name']+'_new')
        self.assertEqual(camera.clip , BASE_URL + config['thumbnail'] + '.mp4_new')
        self.assertEqual(camera.thumbnail, BASE_URL + config['thumbnail'] + '.jpg_new')
        self.assertEqual(camera.temperature, config['temp'] + 10)
        self.assertEqual(camera.battery, config['battery'] + 1)
        self.assertEqual(camera.notifications, config['notifications'] + 1)
        self.assertEqual(camera.image_link, test_img)
        self.assertEqual(camera.arm_link, test_arm)
        self.assertEqual(camera.header, test_header)
        self.assertEqual(camera.motion, test_motion)
        
        # Verify bulk update function
        test_name    = camera.name +' last'
        test_status  = True
        test_url     = '-this-is-a-test/for_realz'
        test_temp    = camera.temperature + 7
        test_battery = camera.battery - 1
        test_notif   = camera.notifications - 1
        values = {'name':test_name, 'armed':test_status, 'thumbnail':test_url, 'temp':test_temp, 'battery':test_battery, 'notifications':test_notif}
        
        camera.update(values)
        # Check that values are properly stored and can be recalled
        jpg_url = BASE_URL + test_url +'.jpg'
        mp4_url = BASE_URL + test_url +'.mp4'
        self.assertEqual(camera.name, test_name)
        self.assertEqual(camera.armed, test_status)
        self.assertEqual(camera.clip, mp4_url)
        self.assertEqual(camera.thumbnail, jpg_url)
        self.assertEqual(camera.temperature, test_temp)
        self.assertEqual(camera.battery, test_battery)
        self.assertEqual(camera.notifications, test_notif)
        