#!/usr/bin/python
import blinkpy

blink = blinkpy.Blink()
blink.login()
blink.setup_system()

for camera in blink.cameras:
    print(camera.name)          # Name of the camera
    print(camera.id)            # Integer id of the camera (assigned by Blink)
    print(camera.armed)        # Whether the device is armed/disarmed (ie. detecting motion)
    print(camera.clip)          # Link to last motion clip captured
    print(camera.thumbnail)     # Link to current camera thumbnail
    print(camera.temperature)   # Current camera temperature (not super accurate, but might be useful for someone)
    print(camera.battery)       # Current battery level... I think the value ranges from 0-3, but not quite sure yet.
    print(camera.notifications) # Number of unread notifications (ie. motion alerts that haven't been viewed)
    print(camera.motion)        # Dictionary containing values for keys ['video', 'image', 'time']
                                # which correspond to last motion recorded, thumbnail of last motion, and timestamp of last motion