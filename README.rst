blinkpy |Build Status| |Coverage Status| |Docs| |PyPi Version| |Python Version|
================================================================================
A Python library for the Blink Camera system

Like the library? Consider buying me a cup of coffee!

|Donate|

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


If you'd like to contribute to this library, please read the `contributing instructions <https://github.com/fronzbot/blinkpy/blob/dev/CONTRIBUTING.md>`__.

For more information on how to use this library, please `read the docs <https://blinkpy.readthedocs.io/en/latest/>`__.

Purpose
===========
This library was built with the intention of allowing easy communication with Blink camera systems, specifically to support the `Blink component <https://home-assistant.io/components/blink>`__ in `homeassistant <https://home-assistant.io/>`__.

Quick Start
=============
The simplest way to use this package from a terminal is to call ``Blink.start()`` which will prompt for your Blink username and password and then log you in.  Alternatively, you can instantiate the Blink class with a username and password, and call ``Blink.start()`` to login and setup without prompt, as shown below.  In addition, http requests are throttled internally via use of the ``Blink.refresh_rate`` variable, which can be set at initialization and defaults to 30 seconds.

.. code:: python

    from blinkpy import blinkpy
    blink = blinkpy.Blink(username='YOUR USER NAME', password='YOUR PASSWORD', refresh_rate=30)
    blink.start()

If you would like to log in without setting up the cameras or system, you can simply call the ``Blink.login()`` function which will prompt for a username and password and then authenticate with the server.  This is useful if you want to avoid use of the ``start()`` function which simply acts as a wrapper for more targeted API methods.

Cameras are instantiated as individual ``BlinkCamera`` classes within a ``BlinkSyncModule`` instance.  All of your sync modules are stored within the ``Blink.sync`` dictionary and can be accessed using the name of the sync module as the key (this is the name of your sync module in the Blink App).

The below code will display cameras and their available attributes:

.. code:: python

    from blinkpy import blinkpy

    blink = blinkpy.Blink(username='YOUR USER NAME', password='YOUR PASSWORD')
    blink.start()

    for name, camera in blink.cameras.items():
      print(name)                   # Name of the camera
      print(camera.attributes)      # Print available attributes of camera

The most recent images and videos can be accessed as a bytes-object via internal variables.  These can be updated with calls to ``Blink.refresh()`` but will only make a request if motion has been detected or other changes have been found.  This can be overridden with the ``force_cache`` flag, but this should be used for debugging only since it overrides the internal request throttling.

.. code:: python
    
    camera = blink.cameras['SOME CAMERA NAME']
    blink.refresh(force_cache=True)  # force a cache update USE WITH CAUTION
    camera.image_from_cache.raw  # bytes-like image object (jpg)
    camera.video_from_cache.raw  # bytes-like video object (mp4)

The ``blinkpy`` api also allows for saving images and videos to a file and snapping a new picture from the camera remotely:

.. code:: python

    camera = blink.cameras['SOME CAMERA NAME']
    camera.snap_picture()       # Take a new picture with the camera
    blink.refresh()             # Get new information from server
    camera.image_to_file('/local/path/for/image.jpg')
    camera.video_to_file('/local/path/for/video.mp4')
    
You can also use this library to download all videos from the server.  In order to do this, you must specify a ``path``.  You may also specifiy a how far back in time to go to retrieve videos via the ``since=`` variable (a simple string such as ``"2017/09/21"`` is sufficient), as well as how many pages to traverse via the ``page=`` variable.  Note that by default, the library will search the first ten pages which is sufficient in most use cases.  Additionally, you can specidy one or more cameras via the ``camera=`` property.  This can be a single string indicating the name of the camera, or a list of camera names.  By default, it is set to the string ``'all'`` to grab videos from all cameras.

Example usage, which downloads all videos recorded since July 4th, 2018 at 9:34am to the ``/home/blink`` directory:

.. code:: python

    blink = blinkpy.Blink(username="YOUR USER NAME", password="YOUR PASSWORD")
    blink.start()
    blink.download_videos('/home/blink', since='2018/07/04 09:34')


.. |Build Status| image:: https://travis-ci.org/fronzbot/blinkpy.svg?branch=dev
   :target: https://travis-ci.org/fronzbot/blinkpy
.. |Coverage Status| image:: https://coveralls.io/repos/github/fronzbot/blinkpy/badge.svg?branch=dev
    :target: https://coveralls.io/github/fronzbot/blinkpy?branch=dev
.. |PyPi Version| image:: https://img.shields.io/pypi/v/blinkpy.svg
    :target: https://pypi.python.org/pypi/blinkpy
.. |Docs| image:: https://readthedocs.org/projects/blinkpy/badge/?version=latest
   :target: http://blinkpy.readthedocs.io/en/latest/?badge=latest
.. |Python Version| image:: https://img.shields.io/pypi/pyversions/blinkpy.svg
   :target: https://img.shields.io/pypi/pyversions/blinkpy.svg
   
.. |Donate| image:: https://www.paypalobjects.com/en_US/i/btn/btn_donateCC_LG.gif
   :target: https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=UR6Z2B8GXYUCC
