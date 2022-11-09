"""Provide functions for enabling infrared illumiation."""

from json import dumps
from blinkpy import api


def get_night_vision_info(camera):
    """Get `night_vision_control` info."""
    if camera.product_type == "owl":
        url = f"{camera.sync.urls.base_url}/api/v1/accounts/{camera.sync.blink.account_id}/networks/{camera.network_id}/owls/{camera.camera_id}/config"
        res = api.http_get(camera.sync.blink, url)
    elif camera.product_type == "catalina":
        url = f"{camera.sync.urls.base_url}/network/{camera.network_id}/camera/{camera.camera_id}/config"
        res = api.http_get(camera.sync.blink, url).get("camera", [{}])[0]
    else:
        return None
    keys = ["night_vision_control", "illuminator_enable", "illuminator_enable_v2"]
    return dict(zip(keys, map(lambda _: res.get(_, None), keys)))


def set_night_vision(camera, to="auto"):
    """
    Set night vision (IR) parameters for a Blink camera.

    :to: new state for the IR illuminator.
         Owl cameras accept "on", "off", and "auto" states,
         whereas Catalina cameras accept 0, 1, or 2 as valid states.
    """
    if camera.product_type == "owl" and to in ["auto", "on", "off"]:
        url = f"{camera.sync.urls.base_url}/api/v1/accounts/{camera.sync.blink.account_id}/networks/{camera.network_id}/owls/{camera.camera_id}/config"
    elif camera.product_type == "catalina" and to in [0, 1, 2]:
        url = f"{camera.sync.urls.base_url}/network/{camera.network_id}/camera/{camera.camera_id}/update"
    else:
        return None
    data = dumps({"illuminator_enable": to})
    res = api.http_post(camera.sync.blink, url, json=False, data=data)
    if res.ok:
        return res.json()
    return None
