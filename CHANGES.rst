=========
Changelog
=========

A list of changes between each release

0.22.3 (2023-11-05)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Bugfixes**

- Check for none and empty dict (fix of home-assistant/core#103312) (`@mkmer #800 <https://github.com/fronzbot/blinkpy/pull/800>`__)

** Other Changes **

- Bump ruff to 0.1.3
- Bump pytest to 7.4.3
- Bump black to 23.10.1


0.22.2 (2023-10-13)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Same as 0.22.1 (pypi upload issue)

0.22.1 (2023-10-13)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Bugfixes**

- Fix night vision toggling for older devices (owl) (`@cocasema #756 <https://github.com/fronzbot/blinkpy/pull/756>`__)
- Add missing await to blinkapp.py (`@mkmer #768 <https://github.com/fronzbot/blinkpy/pull/768>`__)
- Add check command to POST commands (`@mkmer #772 <https://github.com/fronzbot/blinkpy/pull/772>`__)
- Fix blinkapp session call (`@mkmer #783 <https://github.com/fronzbot/blinkpy/pull/783>`__)

**Other Changes**

- Cleanup readme, add breaking change warning
- Migrate to puproject.toml + ruff
- Bump ruff to 0.0.292
- Bump black to 23.9.1
- Bump coverage to 7.3.2
- Bump build to 1.0.3
- Bump pytest to 7.4.2
- Bump pytest-timeout to 2.2.0
- Fix 'stale' github action

0.22.0 (2023-08-16)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Bugfixes**

-None

**New Features**

- Asyncio conversion (`@mkmer #723 <https://github.com/fronzbot/blinkpy/pull/723>`__)

**Other Changes**

- Various fixes to codebase to support asyncio
- Upgrade flake8 to 6.1.0
- Upgrade pylint to 2.17.5
- Upgrade pytest to 7.4.0
- Upgrade black to 23.7.0
- Upgrade pytest-cov to 4.1.0
- Upgrade pygments to 2.16.1
- Upgrade coverage to 7.3.0

0.21.0 (2023-05-28)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Bugfixes**

- None

**New Features**

- Add get_videos_metadata function (`@rhhayward #685 <https://github.com/fronzbot/blinkpy/pull/685>`__)
- Add night vision toggling support (`@jrhunger #717 <https://github.com/fronzbot/blinkpy/pull/717>`__)
- Add doorbell arming functionality (`@mkmer #719 <https://github.com/fronzbot/blinkpy/pull/719>`__)

**Other Changes**

- Upgrade pylint to 2.17.4
- Upgrade coverage to 7.2.5
- Upgrade pygments to 2.15.1
- Upgrade pytest to 7.3.1
- Upgrade pytest-sugar to 0.9.7
- Upgrade black to 23.3.0


0.20.0 (2023-01-29)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Bugfixes**

- Misc doorbell fixes (`@jeffothy #623 <https://github.com/fronzbot/blinkpy/pull/623>`__)

**New Features**

- Add support for local storage API (`@perdue #650 <https://github.com/fronzbot/blinkpy/pull/650>`__)

**Other Changes**

- Deprecate py3.7 (`@fronzbot #644 <https://github.com/fronzbot/blinkpy/pull/644>`__)
- Upgrade pytest to 7.20
- Upgrade pylint to 2.15.10
- Upgrade pre-commit to 3.0.2
- Upgrade black to 22.12.0
- Upgrade flake8 to 6.0.0
- Upgrade coverage to 7.1.0
- Upgrade pydocstyle to 6.3.0
- Upgrade flake8-docstrings to 1.7.0
- Upgrade pygments to 2.14.0
- Upgrade pytest-sugar to 0.9.6


0.19.2 (2022-07-26)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Bugfixes**

- Fix doorbell mapping (`@uvjim #599 <https://github.com/fronzbot/blinkpy/pull/599>`__)
- Fix the errors for the Blink doorbell camera (`@ruby-dev #603 <https://github.com/fronzbot/blinkpy/pull/603>`__)

**Other Changes**

- dev version bump (`@fronzbot #593 <https://github.com/fronzbot/blinkpy/pull/593>`__)
- Fix typo in README regarding disarm syntax (`@dashrb #597 <https://github.com/fronzbot/blinkpy/pull/597>`__)


0.19.1 (2022-06-26)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Bugfixes**

- Fix getting doorbell details (`@uvjim #584 <https://github.com/fronzbot/blinkpy/pull/584>`__)
- Potential fix for mixed camera usage (`@fronzbot #590 <https://github.com/fronzbot/blinkpy/pull/590>`__)

**Other Changes**

- doc update (`@dwaltsch #579 <https://github.com/fronzbot/blinkpy/pull/579>`__)
- Test re-factoring (`@fronzbot #591 <https://github.com/fronzbot/blinkpy/pull/591>`__)
- Bump pylint to 2.14.3
- Bump coverage to 6.41
- Bump black to 22.3.0


0.19.0 (2022-03-20)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Bugfixes:**

- Debug log in prase download method fix (`@tieum #540 <https://github.com/fronzbot/blinkpy/pull/540>`__)
- Fix issue with malformed thumbnails (`@fronzbot #550 <https://github.com/fronzbot/blinkpy/pull/550>`__)
- Fully support new thumbnail API (`@gdoermann #552 <https://github.com/fronzbot/blinkpy/pull/552>`__)

**New Features:**

- Support for arm/disarm of Blink Mini cameras (`@mstratford #546 <https://github.com/fronzbot/blinkpy/pull/546>`__)
- Add product_type to BlinkCamera class to report type of camera (`@fronzbot #553 <https://github.com/fronzbot/blinkpy/pull/553>`__)
- Remove python 3.6 support, add python 3.10 support (`@fronzbot #554 <https://github.com/fronzbot/blinkpy/pull/554>`__)

**Other:**

- Make code that determines need for unique class (Mini + Doorbells) generic (`@fronzbot #553 <https://github.com/fronzbot/blinkpy/pull/553>`__)
- Bump pre-commit to 2.17.0
- Bump pytest-timeout to 2.1.0
- Bump pygments to 2.11.2
- Bump black to 22.1.0
- Bump coverage to 6.3.2
- Bump pytest to 7.1.1
- Bump restructuredtext-lint to 1.4.0


0.18.0 (2021-12-11)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Bugfixes:**

- None

**New Features:**

- Support for Blink Doorbell (`@magicalyak #526 <https://github.com/fronzbot/blinkpy/pull/526>`__)

**Other:**

- Bump pytest-cov to 3.0.0
- Bump pre-commit to 2.15.0
- Bump pytest to 6.2.5
- Bump pylint to 2.10.2
- Bump pygments to 2.10.0
- Bump flake8-docstrings to 1.6.0
- Bump pydocstyle to 6.0.0
- Bump coverage to 5.5


0.17.1 (2021-02-18)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Add delay parameter to Blink.download_videos method in order to throttle API during video retrieval (`@fronzbot #437 <https://github.com/fronzbot/blinkpy/pull/437>`__)
- Bump pylint to 2.6.2


0.17.0 (2021-02-15)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Bugfixes:**

- Fix video downloading bug (`@fronzbot #424 <https://github.com/fronzbot/blinkpy/pull/424>`__)
- Fix repeated authorization email bug (`@fronzbot #432 <https://github.com/fronzbot/blinkpy/pull/432>`__ and `@fronzbot #428 <https://github.com/fronzbot/blinkpy/pull/428>`__)

**New Features:**

- Add logout method (`@fronzbot #429 <https://github.com/fronzbot/blinkpy/pull/429>`__)
- Add camera record method (`@fronzbot #430 <https://github.com/fronzbot/blinkpy/pull/430>`__)

**Other:**

- Add debug script to main repo to help with general debug
- Upgrade login endpoint from v4 to v5
- Add python 3.9 support
- Bump coverage to 5.4
- Bump pytest to 6.2.2
- Bump pytest-cov to 2.11.1
- Bump pygments to 2.8.0
- Bump pre-commit to 2.10.1
- Bump restructuredtext-lint to 1.3.2


0.16.4 (2020-11-22)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Bugfixes:**

- Updated liveview endpoint (`@fronzbot #389 <https://github.com/fronzbot/blinkpy/pull/389>`__)
- Fixed mini thumbnail not updating (`@fronzbot #388 <https://github.com/fronzbot/blinkpy/pull/388>`__)
- Add exception catch to prevent NoneType error on refresh, added test to check behavior as well (`@fronzbot #401 <https://github.com/fronzbot/blinkpy/pull/401>`__)
  - Unrelated: had to add two force methods to refresh for testing purposes. Should not change normal usage.
- Fix malformed stream url (`@fronzbot #395 <https://github.com/fronzbot/blinkpy/pull/395>`__)

**All:**

- Moved testtools to requirements_test.txt (`@fronzbot #387 <https://github.com/fronzbot/blinkpy/pull/387>`__)
- Bumped pytest to 6.1.1
- Bumped flake8 to 3.8.4
- Fixed README spelling (`@rohitsud #381 <https://github.com/fronzbot/blinkpy/pull/381>`__)
- Bumped pygments to 2.7.1
- Bumped coverage to 5.3
- Bumped pydocstyle to 5.1.1
- Bumped pre-commit to 2.7.1
- Bumped pylint to 2.6.0
- Bumped pytest-cov to 2.10.1


0.16.3 (2020-08-02)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Add user-agent to all headers

0.16.2 (2020-08-01)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Add user-agent to header at login
- Remove extra data parameters at login (not-needed)
- Bump pytest to 6.0.1


0.16.1 (2020-07-29)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Unpin requirements, set minimum version instead
- Bump coverage to 5.2.1
- Bump pytest to 6.0.0


0.16.0 (2020-07-20)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Breaking Changes:**

- Add arm property to camera, deprecate motion enable method (`@fronzbot #273 <https://github.com/fronzbot/blinkpy/pull/273>`__)
- Complete refactoring of auth logic (breaks all pre-0.16.0 setups!) (`@fronzbot #261 <https://github.com/fronzbot/blinkpy/pull/261>`__)

**New Features:**

- Add is_errored property to Auth class (`@fronzbot #275 <https://github.com/fronzbot/blinkpy/pull/275>`__)
- Add new endpoint to get user infor (`@fronzbot #280 <https://github.com/fronzbot/blinkpy/pull/280>`__)
- Add get_liveview command to camera module (`@fronzbot #289 <https://github.com/fronzbot/blinkpy/pull/289>`__)
- Add blink Mini Camera support (`@fronzbot #290 <https://github.com/fronzbot/blinkpy/pull/290>`__)
- Add option to skip homescreen check (`@fronzbot #305 <https://github.com/fronzbot/blinkpy/pull/305>`__)
- Add different timeout for video and image retrieval (`@fronzbot #323 <https://github.com/fronzbot/blinkpy/pull/323>`__)
- Modifiy session to use HTTPAdapter and handle retries (`@fronzbot #324 <https://github.com/fronzbot/blinkpy/pull/324>`__)
- Add retry option overrides (`@fronzbot #339 <https://github.com/fronzbot/blinkpy/pull/339>`__)

**All changes:**

Please see the change list in the (`Release Notes <https://github.com/fronzbot/releases/tag/v0.16.0>`__)


0.15.1 (2020-07-11)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- Bugfix: remove "Host" from auth header (`@fronzbot #330 <https://github.com/fronzbot/blinkpy/pull/330>`__)


0.15.0 (2020-05-08)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Breaking Changes:**

- Removed support for Python 3.5 (3.6 is now the minimum supported version)
- Deprecated ``Blink.login()`` method.  Please only use the ``Blink.start()`` method for logging in.

**New Functions**

- Add ``device_id`` override when logging in (for debug and to differentiate applications) (`@fronzbot #245 <https://github.com/fronzbot/blinkpy/pull/245>`__)

This can be used by instantiating the Blink class with the ``device_id`` parameter. 

**All Changes:**

- Fix setup.py use of internal pip structure (`@fronzbot #233 <https://github.com/fronzbot/blinkpy/pull/233>`__)
- Update python-slugify requirement from ~=3.0.2 to ~=4.0.0 (`@fronzbot #234 <https://github.com/fronzbot/blinkpy/pull/234>`__)
- Update python-dateutil requirement from ~=2.8.0 to ~=2.8.1 (`@fronzbot #230 <https://github.com/fronzbot/blinkpy/pull/230>`__)
- Bump requests from 2.22.0 to 2.23.0 (`@fronzbot #231 <https://github.com/fronzbot/blinkpy/pull/231>`__)
- Refactor login logic in preparation for 2FA (`@fronzbot #241 <https://github.com/fronzbot/blinkpy/pull/241>`__)
- Add 2FA Support (`@fronzbot #242 <https://github.com/fronzbot/blinkpy/pull/242>`__) (fixes (`#210 <https://github.com/fronzbot/blinkpy/pull/210>`__))
- Re-set key_required and available variables after setup (`@fronzbot #245 <https://github.com/fronzbot/blinkpy/pull/245>`__) 
- Perform system refresh after setup (`@fronzbot #245 <https://github.com/fronzbot/blinkpy/pull/245>`__)
- Fix typos (`@fronzbot #244 <https://github.com/fronzbot/blinkpy/pull/244>`__)

0.14.3 (2020-04-22)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- Add time check on recorded videos before determining motion
- Fix motion detection variable suck to ``True``
- Add ability to load credentials from a json file
- Only allow ``motion_detected`` variable to trigger if system was armed
- Log response message from server if not attempting a re-authorization

0.14.2 (2019-10-12)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- Update dependencies
- Dockerize (`@3ch01c #198 <https://github.com/fronzbot/blinkpy/pull/198>`__)

0.14.1 (2019-06-20)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- Fix timeout problems blocking blinkpy startup
- Updated login urls using ``rest-region`` subdomain
- Removed deprecated thumbanil recovery from homescreen

0.14.0 (2019-05-23)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Breaking Changes:**

- ``BlinkCamera.battery`` no longer reports a percentage, instead it returns a string representing the state of the battery.
- Previous logic for calculating percentage was incorrect
- raw battery voltage can be accessed via ``BlinkCamera.battery_voltage``

**Bug Fixes:**

- Updated video endpoint (fixes broken motion detection)
- Removed throttling from critical api methods which prevented proper operation of multi-sync unit setups
- Slugify downloaded video names to allow for OS interoperability
- Added one minute offset (``Blink.motion_interval``) when checking for recent motion to allow time for events to propagate to server prior to refresh call.

**Everything else:**

- Changed all urls to use ``rest-region`` rather than ``rest.region``.  Ability to revert to old method is enabled by instantiating ``Blink()`` with the ``legacy_subdomain`` variable set to ``True``.
- Added debug mode to ``blinkpy.download_videos`` routine to simply print the videos prepped for download, rather than actually saving them.
- Use UTC for time conversions, rather than local timezone


0.13.1 (2019-03-01)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- Remove throttle decorator from network status request

0.13.0 (2019-03-01)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Breaking change:**
Wifi status reported in dBm again, instead of bars (which is great).  Also, the old ``get_camera_info`` method has changed and requires a ``camera_id`` parameter.

- Adds throttle decorator
- Decorate following functions with 4s throttle (call method with ``force=True`` to override):
    - request_network_status
    - request_syncmodule
    - request_system_arm
    - request_system_disarm
    - request_sync_events
    - request_new_image
    - request_new_video
    - request_video_count
    - request_cameras
    - request_camera_info
    - request_camera_sensors
    - request_motion_detection_enable
    - request_motion_detection_disable
- Use the updated homescreen api endpoint to retrieve camera information.  The old method to retrieve all cameras at once seems to not exist, and this was the only solution I could figure out and confirm to work.
- Adds throttle decorator to refresh function to prevent too many frequent calls with ``force_cache`` flag set to ``True``.  This additional throttle can be overridden with the ``force=True`` argument passed to the refresh function.
- Add ability to cycle through login api endpoints to anticipate future endpoint deprecation


0.12.1 (2019-01-31)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- Remove logging improvements since they were incompatible with home-assistant logging

0.12.0 (2019-01-31)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- Fix video api endpoint, re-enables motion detection
- Add improved logging capability
- Add download video method
- Prevent blinkpy from failing at setup due to api error


0.11.2 (2019-01-23)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- Hotfix to prevent platform from stalling due to API change
- Motion detection and video recovery broken until new API endpoint discovered

0.11.1 (2019-01-02)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- Fixed incorrect backup login url
- Added calibrated temperature property for cameras


0.11.0 (2018-11-23)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- Added support for multiple sync modules

0.10.3 (2018-11-18)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- Use networks endpoint rather than homecreen to retrieve arm/disarm status (`@md-reddevil <https://github.com/fronzbot/blinkpy/pull/119>`__)
- Fix incorrect command status endpoint (`@md-reddevil <https://github.com/fronzbot/blinkpy/pull/118>`__)
- Add extra debug logging
- Remove error prior to re-authorization (only log error when re-auth failed)


0.10.2 (2018-10-30)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- Set minimum required version of the requests library to 2.20.0 due to vulnerability in earlier releases.
- When multiple networks detected, changed log level to ``warning`` from ``error`` 


0.10.1 (2018-10-18)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- Fix re-authorization bug (fixes `#101 <https://github.com/fronzbot/blinkpy/issues/#101>`__)
- Log an error if saving video that doesn't exist

0.10.0 (2018-10-16)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- Moved all API calls to own module for easier maintainability
- Added network ids to sync module and cameras to allow for multi-network use
- Removed dependency on video existance prior to camera setup (fixes `#93 <https://github.com/fronzbot/blinkpy/issues/#93>`__)
- Camera wifi_strength now reported in wifi "bars" rather than dBm due to API endpoint change
- Use homescreen thumbnail as fallback in case it's not in the camera endpoint
- Removed "armed" and "status" attributes from camera (status of camera only reported by "motion_enabled" now)
- Added serial number attributes to sync module and cameras
- Check network_id from login response and verify that network is onboarded (fixes `#90 <https://github.com/fronzbot/#90>`__)
- Check if retrieved clip is "None" prior to storing in cache

0.9.0 (2018-09-27)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- Complete code refactoring to enable future multi-sync module support
- Add image and video caching to the cameras
- Add internal throttling of system refresh
- Use session for http requests

**Breaking change:**
- Cameras now accessed through sync module ``Blink.sync.cameras``


0.8.1 (2018-09-24)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
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
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- Added support for battery voltage level (fixes `#64 <https://github.com/fronzbot/blinkpy/issues/64>`__)
- Added motion detection per camera
- Added fully accessible camera configuration dict
- Added celcius property to camera (fixes `#60 <https://github.com/fronzbot/blinkpy/issues/60>`__)

0.7.1 (2018-05-09)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- Fixed pip 10 import issue during setup (`@fronzbot <https://github.com/fronzbot/blinkpy/pull/61>`__)

0.7.0 (2018-02-08)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- Fixed style errors for bumped pydocstring and pylint versions
- Changed Blink.cameras dictionary to be case-insensitive (fixes `#35 <https://github.com/fronzbot/blinkpy/issues/35>`__)
- Changed api endpoint for video extraction (fixes `#35 <https://github.com/fronzbot/blinkpy/issues/35>`__ and `#41 <https://github.com/fronzbot/blinkpy/issues/41>`__)
- Removed last_motion() function from Blink class
- Refactored code for better organization
- Moved some request calls out of @property methods (enables future CLI support)
- Renamed get_summary() method to summary and changed to @property
- Added ability to download most recent video clip
- Improved camera arm/disarm handling (`@b10m <https://github.com/fronzbot/blinkpy/pull/50>`__)
- Added authentication to ``login()`` function and deprecated ``setup_system()`` in favor of ``start()``
- Added ``attributes`` dictionary to camera object

0.6.0 (2017-05-12)
~~~~~~~~~~~~~~~~~~
- Removed redundent properties that only called hidden variables
- Revised request wrapper function to be more intelligent
- Added tests to ensure exceptions are caught and handled (100% coverage!)
- Added auto-reauthorization (token refresh) when a request fails due to an expired token (`@tySwift93 <https://github.com/fronzbot/blinkpy/pull/24>`__)
- Added battery level string to reduce confusion with the way Blink reports battery level as integer from 0 to 3

0.5.2 (2017-03-12)
~~~~~~~~~~~~~~~~~~
- Fixed packaging mishap, same as 0.5.0 otherwise

0.5.0 (2017-03-12)
~~~~~~~~~~~~~~~~~~
- Fixed region handling problem
- Added rest.piri subdomain as a backup if region can't be found
- Improved the file writing function
- Large test coverage increase

0.4.4 (2017-03-06)
~~~~~~~~~~~~~~~~~~
- Fixed bug where region id was not being set in the header

0.4.3 (2017-03-05)
~~~~~~~~~~~~~~~~~~
- Changed to bdist_wheel release

0.4.2 (2017-01-28)
~~~~~~~~~~~~~~~~~~
- Fixed inability to retrieve motion data due to Key Error

0.4.1 (2017-01-27)
~~~~~~~~~~~~~~~~~~
- Fixed refresh bug (0.3.1 did not actually fix the problem)
- Image refresh routine added (per camera)
- Dictionary of thumbnails per camera added
- Improved test coverage

0.3.1 (2017-01-25)
~~~~~~~~~~~~~~~~~~
- Fixed refresh bug (Key Error)

0.3.0 (2017-01-25)
~~~~~~~~~~~~~~~~~~
- Added device id to camera lookup table
- Added image to file method

0.2.0 (2017-01-21)
~~~~~~~~~~~~~~~~~~
- Initial release of blinkpy
