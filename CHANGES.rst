Changelog
-----------

A list of changes between each release

0.10.2 (2018-10-30)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
- Set minimum required version of the requests library to 2.20.0 due to vulnerability in earlier releases.
- When multiple networks detected, changed log level to 'warning' from 'error' 


0.10.1 (2018-10-18)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
- Fix re-authorization bug (fixes `#101 <https://github.com/fronzbot/blinkpy/issues/#101>`_)
- Log an error if saving video that doesn't exist

0.10.0 (2018-10-16)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
- Moved all API calls to own module for easier maintainability
- Added network ids to sync module and cameras to allow for multi-network use
- Removed dependency on video existance prior to camera setup (fixes `#93 <https://github.com/fronzbot/blinkpy/issues/#93>`_)
- Camera wifi_strength now reported in wifi "bars" rather than dBm due to API endpoint change
- Use homescreen thumbnail as fallback in case it's not in the camera endpoint
- Removed "armed" and "status" attributes from camera (status of camera only reported by "motion_enabled" now)
- Added serial number attributes to sync module and cameras
- Check network_id from login response and verify that network is onboarded (fixes `#90 <https://github.com/fronzbot/#90>`_)
- Check if retrieved clip is "None" prior to storing in cache

0.9.0 (2018-09-27)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
- Complete code refactoring to enable future multi-sync module support
- Add image and video caching to the cameras
- Add internal throttling of system refresh
- Use session for http requests

**Breaking change:**
- Cameras now accessed through sync module Blink.sync.cameras


0.8.1 (2018-09-24)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
- Update requirements_test.txt
- Update linter versions
- Fix pylint warnings
  - Remove object from class declarations
  - Remove useless returns from functions
- Fix pylint errors
  - change if comparison to fix (consider-using-in)
  - Disabled no else-if-return check
- Fix useless-import-alias
- Disable no-else-return
- Fix motion detection
  - Use an array of recent video clips to determine if motion has been detected.
  - Reset the value every system refresh

0.8.0 (2018-05-21)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
- Added support for battery voltage level (fixes `#64 <https://github.com/fronzbot/blinkpy/issues/64>`_)
- Added motion detection per camera
- Added fully accessible camera configuration dict
- Added celcius property to camera (fixes `#60 <https://github.com/fronzbot/blinkpy/issues/60>`_)

0.7.1 (2018-05-09)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
- Fixed pip 10 import issue during setup (`@fronzbot <https://github.com/fronzbot/blinkpy/pull/61>`_)

0.7.0 (2018-02-08)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
- Fixed style errors for bumped pydocstring and pylint versions
- Changed Blink.cameras dictionary to be case-insensitive (fixes `#35 <https://github.com/fronzbot/blinkpy/issues/35>`_)
- Changed api endpoint for video extraction (fixes `#35 <https://github.com/fronzbot/blinkpy/issues/35>`_ and `#41 <https://github.com/fronzbot/blinkpy/issues/41>`_)
- Removed last_motion() function from Blink class
- Refactored code for better organization
- Moved some request calls out of @property methods (enables future CLI support)
- Renamed get_summary() method to summary and changed to @property
- Added ability to download most recent video clip
- Improved camera arm/disarm handling (`@b10m <https://github.com/fronzbot/blinkpy/pull/50>`_)
- Added authentication to ``login()`` function and deprecated ``setup_system()`` in favor of ``start()``
- Added ``attributes`` dictionary to camera object

0.6.0 (2017-05-12)
^^^^^^^^^^^^^^^^^^
- Removed redundent properties that only called hidden variables
- Revised request wrapper function to be more intelligent
- Added tests to ensure exceptions are caught and handled (100% coverage!)
- Added auto-reauthorization (token refresh) when a request fails due to an expired token (`@tySwift93 <https://github.com/fronzbot/blinkpy/pull/24>`_)
- Added battery level string to reduce confusion with the way Blink reports battery level as integer from 0 to 3

0.5.2 (2017-03-12)
^^^^^^^^^^^^^^^^^^
- Fixed packaging mishap, same as 0.5.0 otherwise

0.5.0 (2017-03-12)
^^^^^^^^^^^^^^^^^^
- Fixed region handling problem
- Added rest.piri subdomain as a backup if region can't be found
- Improved the file writing function
- Large test coverage increase

0.4.4 (2017-03-06)
^^^^^^^^^^^^^^^^^^
- Fixed bug where region id was not being set in the header

0.4.3 (2017-03-05)
^^^^^^^^^^^^^^^^^^
- Changed to bdist_wheel release

0.4.2 (2017-01-28)
^^^^^^^^^^^^^^^^^^
- Fixed inability to retrieve motion data due to Key Error

0.4.1 (2017-01-27)
^^^^^^^^^^^^^^^^^^
- Fixed refresh bug (0.3.1 did not actually fix the problem)
- Image refresh routine added (per camera)
- Dictionary of thumbnails per camera added
- Improved test coverage

0.3.1 (2017-01-25)
^^^^^^^^^^^^^^^^^^
- Fixed refresh bug (Key Error)

0.3.0 (2017-01-25)
^^^^^^^^^^^^^^^^^^
- Added device id to camera lookup table
- Added image to file method

0.2.0 (2017-01-21)
^^^^^^^^^^^^^^^^^^
- Initial release of blinkpy
