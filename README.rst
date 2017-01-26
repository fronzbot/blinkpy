**blinkpy**
============
A Python library for the Blink Camera system

**Disclaimers**
===============
Published under the MIT license - See LICENSE file for more details.

"Blink Wire-Free HS Home Monitoring & Alert Systems" is a trademark owned by Immedia Inc., see www.blinkforhome.com for more information.
I am in no way affiliated with Blink, nor Immedia Inc.

Original protocol hacking by MattTW : https://github.com/MattTW/BlinkMonitorProtocol

**Installation**
================
``pip3 install blinkpy``

**Purpose**
===========
This library was built with the intention of allowing easy communication with Blink camera systems, specifically so I can add a module into homeassistant https://home-assistant.io

**Usage**
=========
In terms of usage, you just need to instantiate the module with a username and password
::
  import blinkpy
  blink = blinkpy.Blink(username='YOUR USER NAME', password='YOUR PASSWORD')


If you leave out either of those parameters, you need to call the login function which will prompt for your username and password
::
  blink.login()


Once the login information is entered, you can run the `setup_system()` function which will attempt to authenticate with Blink servers using your username and password, obtain network ids, and create a list of cameras.
The cameras are of a BlinkCamera class, of which the following parameters can be used (the code below creates a Blink object and iterates through each camera found)
::
  blink = blinkpy.Blink(username='YOUR USER NAME', password='YOUR PASSWORD')
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


**class Blink**
---------------
The following properties/methods are availiable to the Blink class

**Blink.cameras**
Returns a list of BlinkCamera objects found by the system

**Blink.network_id**
Returns the current network id

**Blink.account_id**
Returns the account id

**Blink.events**
Returns a list of events recorded by blink.  This information will contain links to any motion caught by an armed camera.

**Blink.online**
Returns online status of sync module (True = online, False = offline)

**Blink.last_motion()**
Finds last motion information for each camera and stores it in the BlinkCamera.motion field

**Blink.arm**
Set to True to arm, False to disarm.  Can be used to see the status of the system as well

**Blink.refresh()**
Forces a refresh of all camera information

**Blink.get_summary()**
Returns json formatted summary of the system

**Blink.get_cameras()**
Finds all cameras in the system and creates them

**Blink.set_links()**
Gives each BlinkCamera object the links needed to find recent images and videos

**Blink.login()**
Prompts user for login information

**Blink.get_auth_token()**
Uses login information to retrieve authorization token from Blink for further communication

**Blink.get_ids()**
Retrieves the network_id and account_id from Blink in order to access video and image pages on their server

**Blink.setup_system()**
A wrapper script that calls:
::
  self.get_auth_token()
  self.get_ids()
  self.get_camers()
  self.set_links()


**class BlinkCamera**
---------------------
This class is just a wrapper for each individual camera in order to make communication with individual cameras less clunky.  The following properties/methods are availiable (in addition to the ones mentioned earlier)

**BlinkCamera.snap_picture()**
Takes an image with the camera and saves it as the new thumbnail.  The Blink.refresh() method should be called after this if you want to store the new thumbnail link

**BlinkCamera.set_motion_detect(enable=True/False)**
Sending True to this function will enable motion detection for the camera.  Setting to False will disable motion detection

**BlinkCamera.image_to_file(path)**
This will write the current thumbnail to the location indicated in 'path'








