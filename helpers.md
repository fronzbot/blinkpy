# Helper Functions

## IR/ Night Vision settings

There are helper functions that provide the ability to turn on and off the IR illuminator on Blink cameras. This allows for capturing IR images when needed.

```py
from blinkpy.helpers import camera

# Assume `test_cam` is a valid BlinkCamera object
# Get the current IR status.
camera.get_night_vision_info(test_cam)

# Change the IR light
camera.set_night_vision(test_cam, "off")
```
