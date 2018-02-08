blinkpy |Build Status| |Coverage Status| |Docs|  |PyPi Version|
================================================================
A Python library for the Blink Camera system
Only compatible with Python 3+

Disclaimer:
~~~~~~~~~~~~~~~
Published under the MIT license - See LICENSE file for more details.

"Blink Wire-Free HS Home Monitoring & Alert Systems" is a trademark owned by Immedia Inc., see www.blinkforhome.com for more information.
I am in no way affiliated with Blink, nor Immedia Inc.

Original protocol hacking by MattTW : https://github.com/MattTW/BlinkMonitorProtocol

API calls faster than 60 seconds is not recommended as it can overwhelm Blink's servers.  Please use this module responsibly.

Installation
================
``pip3 install blinkpy``

Installing Development Version
==================================
To install the current development version, perform the following steps.  Note that the following will create a blinkpy directory in your home area:

.. code:: bash

    $ cd ~
    $ git clone https://github.com/fronzbot/blinkpy.git
    $ cd blinkpy
    $ rm -rf build dist
    $ python3 setup.py bdist_wheel
    $ pip3 install --upgrade dist/*.whl


Purpose
===========
This library was built with the intention of allowing easy communication with Blink camera systems, specifically so I can add a module into homeassistant https://home-assistant.io

Usage
=========
The simplest way to use this package from a terminal is to call ``Blink.start()`` which will prompt for your Blink username and password and then log you in.  Alternatively, you can instantiate the Blink class with a username and password, and call ``Blink.start()`` to login and setup without prompt, as shown below.

.. code:: python

    import blinkpy
    blink = blinkpy.Blink(username='YOUR USER NAME', password='YOUR PASSWORD')
    blink.start()

If you would like to log in without setting up the cameras or system, you can simply call the ``Blink.login()`` function which will prompt for a username and password and then authenticate with the server.  This is useful if you want to avoid use of the ``start()`` function which simply acts as a wrapper for more targeted API methods.

The cameras are of a BlinkCamera class, of which the following parameters can be used (the code below creates a Blink object and iterates through each camera found)

.. code:: python

    import blinkpy
    
    blink = blinkpy.Blink(username='YOUR USER NAME', password='YOUR PASSWORD')
    blink.start()
    
    for name, camera in blink.cameras.items():
        print(name)                  # Name of the camera
        print(camera.id)             # Integer id of the camera (assigned by Blink)
        print(camera.armed)          # Whether the device is armed/disarmed (ie. detecting motion)
        print(camera.clip)           # Link to last motion clip captured
        print(camera.thumbnail)      # Link to current camera thumbnail
        print(camera.temperature)    # Current camera temperature (not super accurate, but might be useful for someone)
        print(camera.battery)        # Current battery level... I think the value ranges from 0-3, but not quite sure yet.
        print(camera.battery_string) # Gives battery level as a string ("OK" or "Low").  Returns "Unknown" if value is... well, unknown 
        print(camera.notifications)  # Number of unread notifications (ie. motion alerts that haven't been viewed)


.. |Build Status| image:: https://travis-ci.org/fronzbot/blinkpy.svg?branch=dev
   :target: https://travis-ci.org/fronzbot/blinkpy
.. |Coverage Status| image:: https://coveralls.io/repos/github/fronzbot/blinkpy/badge.svg?branch=dev
    :target: https://coveralls.io/github/fronzbot/blinkpy?branch=dev
.. |PyPi Version| image:: https://img.shields.io/pypi/v/blinkpy.svg
    :target: https://pypi.python.org/pypi/blinkpy
.. |Docs| image:: https://readthedocs.org/projects/blinkpy/badge/?version=latest
   :target: http://blinkpy.readthedocs.io/en/latest/?badge=latest
