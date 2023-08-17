blinkpy |Build Status| |Coverage Status| |Docs| |PyPi Version| |Codestyle|
=============================================================================================
A Python library for the Blink Camera system (Python 3.8+)

Like the library? Consider buying me a cup of coffee!

`Buy me a Coffee! <https://buymeacoffee.com/kevinfronczak>`__

**Disclaimer:**
Published under the MIT license - See LICENSE file for more details.

"Blink Wire-Free HS Home Monitoring & Alert Systems" is a trademark owned by Immedia Inc., see www.blinkforhome.com for more information.
I am in no way affiliated with Blink, nor Immedia Inc.

Original protocol hacking by MattTW : https://github.com/MattTW/BlinkMonitorProtocol

API calls faster than 60 seconds is not recommended as it can overwhelm Blink's servers.  Please use this module responsibly.

Installation
-------------
``pip install blinkpy``

Installing Development Version
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
To install the current development version, perform the following steps.  Note that the following will create a blinkpy directory in your home area:

.. code:: bash

    $ cd ~
    $ git clone https://github.com/fronzbot/blinkpy.git
    $ cd blinkpy
    $ rm -rf build dist
    $ python3 setup.py bdist_wheel
    $ pip3 install --upgrade dist/*.whl


If you'd like to contribute to this library, please read the `contributing instructions <https://github.com/fronzbot/blinkpy/blob/dev/CONTRIBUTING.rst>`__.

For more information on how to use this library, please `read the docs <https://blinkpy.readthedocs.io/en/latest/>`__.

Purpose
-------
This library was built with the intention of allowing easy communication with Blink camera systems, specifically to support the `Blink component <https://home-assistant.io/components/blink>`__ in `homeassistant <https://home-assistant.io/>`__.

Quick Start
=============
The simplest way to use this package from a terminal is to call ``await Blink.start()`` which will prompt for your Blink username and password and then log you in.  In addition, http requests are throttled internally via use of the ``Blink.refresh_rate`` variable, which can be set at initialization and defaults to 30 seconds.

.. code:: python

    from blinkpy.blinkpy import Blink
   
    blink = Blink()
    await blink.start()


This flow will prompt you for your username and password.  Once entered, if you likely will need to send a 2FA key to the blink servers (this pin is sent to your email address).  When you receive this pin, enter at the prompt and the Blink library will proceed with setup.

Starting blink without a prompt
-------------------------------
In some cases, having an interactive command-line session is not desired.  In this case, you will need to set the ``Blink.auth.no_prompt`` value to ``True``.  In addition, since you will not be prompted with a username and password, you must supply the login data to the blink authentication handler.  This is best done by instantiating your own auth handler with a dictionary containing at least your username and password.

.. code:: python

    from blinkpy.blinkpy import Blink
    from blinkpy.auth import Auth

    blink = Blink()
    # Can set no_prompt when initializing auth handler
    auth = Auth({"username": <your username>, "password": <your password>}, no_prompt=True)
    blink.auth = auth
    await blink.start()


Since you will not be prompted for any 2FA pin, you must call the ``blink.auth.send_auth_key`` function.  There are two required parameters: the ``blink`` object as well as the ``key`` you received from Blink for 2FA:

.. code:: python

    await auth.send_auth_key(blink, <your key>)
    await blink.setup_post_verify()


Supplying credentials from file
--------------------------------
Other use cases may involved loading credentials from a file.  This file must be ``json`` formatted and contain a minimum of ``username`` and ``password``.  A built in function in the ``blinkpy.helpers.util`` module can aid in loading this file.  Note, if ``no_prompt`` is desired, a similar flow can be followed as above.

.. code:: python

    from blinkpy.blinkpy import Blink
    from blinkpy.auth import Auth
    from blinkpy.helpers.util import json_load

    blink = Blink()
    auth = Auth(await json_load("<File Location>"))
    blink.auth = auth
    await blink.start()


Saving credentials
-------------------
This library also allows you to save your credentials to use in future sessions.  Saved information includes authentication tokens as well as unique ids which should allow for a more streamlined experience and limits the frequency of login requests.  This data can be saved as follows (it can then be loaded by following the instructions above for supplying credentials from a file):

.. code:: python

    await blink.save("<File location>")


Getting cameras
----------------
Cameras are instantiated as individual ``BlinkCamera`` classes within a ``BlinkSyncModule`` instance.  All of your sync modules are stored within the ``Blink.sync`` dictionary and can be accessed using the name of the sync module as the key (this is the name of your sync module in the Blink App).

The below code will display cameras and their available attributes:

.. code:: python

    for name, camera in blink.cameras.items():
      print(name)                   # Name of the camera
      print(camera.attributes)      # Print available attributes of camera


The most recent images and videos can be accessed as a bytes-object via internal variables.  These can be updated with calls to ``Blink.refresh()`` but will only make a request if motion has been detected or other changes have been found.  This can be overridden with the ``force`` flag, but this should be used for debugging only since it overrides the internal request throttling.

.. code:: python
    
    camera = blink.cameras['SOME CAMERA NAME']
    await blink.refresh(force=True)  # force a cache update USE WITH CAUTION
    camera.image_from_cache  # bytes-like image object (jpg)
    camera.video_from_cache  # bytes-like video object (mp4)

The ``blinkpy`` api also allows for saving images and videos to a file and snapping a new picture from the camera remotely:

.. code:: python

    camera = blink.cameras['SOME CAMERA NAME']
    await camera.snap_picture()       # Take a new picture with the camera
    await blink.refresh()             # Get new information from server
    await camera.image_to_file('/local/path/for/image.jpg')
    await camera.video_to_file('/local/path/for/video.mp4')


Arming Blink
-------------
Methods exist to arm/disarm the sync module, as well as enable/disable motion detection for individual cameras.  This is done as follows:

.. code:: python

    # Arm a sync module
    await blink.sync["SYNC MODULE NAME"].async_arm(True)

    # Disarm a sync module
    await blink.sync["SYNC MODULE NAME"].async_arm(False)

    # Print arm status of a sync module - a system refresh should be performed first
    await blink.refresh()
    sync = blink.sync["SYNC MODULE NAME"]
    print(f"{sync.name} status: {sync.arm}")

Similar methods exist for individual cameras:

.. code:: python

   camera = blink.cameras["SOME CAMERA NAME"]

   # Enable motion detection on a camera
   await camera.async_arm(True)

   # Disable motion detection on a camera
   await camera.async_arm( False)

   # Print arm status of a sync module - a system refresh should be performed first
   await blink.refresh()
   print(f"{camera.name} status: {camera.arm}")


Download videos
----------------
You can also use this library to download all videos from the server.  In order to do this, you must specify a ``path``.  You may also specifiy a how far back in time to go to retrieve videos via the ``since=`` variable (a simple string such as ``"2017/09/21"`` is sufficient), as well as how many pages to traverse via the ``stop=`` variable.  Note that by default, the library will search the first ten pages which is sufficient in most use cases.  Additionally, you can specify one or more cameras via the ``camera=`` property.  This can be a single string indicating the name of the camera, or a list of camera names.  By default, it is set to the string ``'all'`` to grab videos from all cameras. If you are downloading many items, setting the ``delay`` parameter is advised in order to throttle sequential calls to the API. By default this is set to ``1`` but can be any integer representing the number of seconds to delay between calls.

Example usage, which downloads all videos recorded since July 4th, 2018 at 9:34am to the ``/home/blink`` directory with a 2s delay between calls:

.. code:: python

    await blink.download_videos('/home/blink', since='2018/07/04 09:34', delay=2)


Sync Module Local Storage
=========================

Description of how I think the local storage API is used by Blink
-----------------------------------------------------------------

Since local storage is within a customer's residence, there are no guarantees for latency
and availability.  As a result, the API seems to be built to deal with these conditions.

In general, the approach appears to be this:  The Blink app has to query the sync
module for all information regarding the stored clips.  On a click to view a clip, the app asks
for the full list of stored clips, finds the clip in question, uploads the clip to the
cloud, and then downloads the clip back from a cloud URL. Each interaction requires polling for
the response since networking conditions are uncertain.  The app also caches recent clips and the manifest.

API steps
---------
1. Request the local storage manifest be created by the sync module.

   * POST **{base_url}/api/v1/accounts/{account_id}/networks/{network_id}/sync_modules/{sync_id}/local_storage/manifest/request**
   * Returns an ID that is used to get the manifest.

2. Retrieve the local storage manifest.

   * GET **{base_url}/api/v1/accounts/{account_id}/networks/{network_id}/sync_modules/{sync_id}/local_storage/manifest/request/{manifest_request_id}**
   * Returns full manifest.
   * Extract the manifest ID from the response.

3. Find a clip ID in the clips list from the manifest to retrieve, and request an upload.

   * POST **{base_url}/api/v1/accounts/{account_id}/networks/{network_id}/sync_modules/{sync_id}/local_storage/manifest/{manifest_id}/clip/request/{clip_id}**
   * When the response is returned, the upload has finished.

4. Download the clip using the same clip ID.

   * GET **{base_url}/api/v1/accounts/{account_id}/networks/{network_id}/sync_modules/{sync_id}/local_storage/manifest/{manifest_id}/clip/request/{clip_id}**



.. |Build Status| image:: https://github.com/fronzbot/blinkpy/workflows/build/badge.svg
   :target: https://github.com/fronzbot/blinkpy/actions?query=workflow%3Abuild
.. |Coverage Status| image:: https://codecov.io/gh/fronzbot/blinkpy/branch/dev/graph/badge.svg
    :target: https://codecov.io/gh/fronzbot/blinkpy
.. |PyPi Version| image:: https://img.shields.io/pypi/v/blinkpy.svg
    :target: https://pypi.python.org/pypi/blinkpy
.. |Docs| image:: https://readthedocs.org/projects/blinkpy/badge/?version=latest
   :target: http://blinkpy.readthedocs.io/en/latest/?badge=latest   
.. |Codestyle| image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black
