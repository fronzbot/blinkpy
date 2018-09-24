Changelog
-----------

A list of changes between each release

0.9.0.dev (Development Version)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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
