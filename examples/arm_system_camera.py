#!/usr/bin/python
import blinkpy
import time

blink = blinkpy.Blink()
blink.login()
blink.setup_system()

for camera in blink.cameras:
    print('Arming ' + camera.name)
    camera.set_motion_detect(True)
    time.sleep(5)
    blink.refresh()

print('Arming Blink')
blink.arm = True
time.sleep(5)
print('Blink armed? ' + str(blink.arm))
print('Disarming Blink')
time.sleep(5)
blink.arm = False
print('Blink armed? ' + str(blink.arm))
