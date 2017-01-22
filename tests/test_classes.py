import testtools
import blinkpy
from blinkpy import BASE_URL

class TestBlink(testtools.TestCase):
    def test_blink_instance(self):
        blink = blinkpy.Blink()
        
    def test_blink_camera_attributes(self):
        test_name    = 'name'
        test_id      = 1248
        test_status  = True
        test_url     = 'https://www.abcdef.com/abc/123/abc456/_-()98~/X.jpg'
        test_temp    = 70
        test_battery = 3
        test_notif   = 0
        camera = blinkpy.BlinkCamera(test_name, test_id, test_status, test_url, test_url, test_temp, test_battery, test_notif)
        
        # Check that values are properly stored and can be recalled
        assert camera.name is test_name
        assert camera.id is test_id
        assert camera.armed is test_status
        assert camera.clip is test_url
        assert camera.thumbnail is test_url
        assert camera.temperature is test_temp
        assert camera.battery is test_battery
        assert camera.notifications is test_notif
        
        # Check that values can be changed with individual methods
        test_name    = test_name +'new'
        test_url     = test_url + '/NEWAPPEND'
        test_temp    = test_temp - 10
        test_battery = test_battery - 1
        test_notif   = test_notif + 3
        test_header  = {'Header':'test','Test':'1234'}
        test_img     = 'http://image-link.com'
        test_arm     = 'http://arm-link.com'
        test_motion  = {'video':'url','image':'url','time':'timestamp'}
        
        camera.name  = test_name
        camera.clip  = test_url
        camera.thumbnail = test_url
        camera.temperature = test_temp
        camera.battery = test_battery
        camera.notifications = test_notif
        camera.image_link = test_img
        camera.arm_link = test_arm
        camera.header = test_header
        camera.motion = test_motion
        
        # Check that values are properly stored and can be recalled
        assert camera.name is test_name
        assert camera.id is test_id
        assert camera.armed is test_status
        assert camera.clip is test_url
        assert camera.thumbnail is test_url
        assert camera.temperature is test_temp
        assert camera.battery is test_battery
        assert camera.notifications is test_notif
        assert camera.header is test_header
        assert camera.image_link is test_img
        assert camera.arm_link is test_arm
        assert camera.motion is test_motion
        
        # Verify bulk update function
        test_name    = test_name +' last'
        test_status  = True
        test_url     = '-this-is-a-test/for_realz'
        test_temp    = test_temp + 7
        test_battery = test_battery - 1
        test_notif   = test_notif - 1
        values = {'name':test_name, 'armed':test_status, 'thumbnail':test_url, 'temp':test_temp, 'battery':test_battery, 'notifications':test_notif}
        
        camera.update(values)
        # Check that values are properly stored and can be recalled
        jpg_url = BASE_URL + test_url +'.jpg'
        mp4_url = BASE_URL + test_url +'.mp4'
        assert camera.name is test_name
        assert camera.id is test_id
        assert camera.armed is test_status
        assert camera.clip == mp4_url
        assert camera.thumbnail == jpg_url
        assert camera.temperature is test_temp
        assert camera.battery is test_battery
        assert camera.notifications is test_notif
        