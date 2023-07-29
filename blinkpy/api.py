"""Implements known blink API calls."""

from __future__ import annotations
from typing import TYPE_CHECKING
import logging
import string
from json import dumps
from aiohttp import ClientResponse
from blinkpy.helpers.util import (
    get_time,
    Throttle,
    local_storage_clip_url_template,
)
from blinkpy.helpers.constants import DEFAULT_URL, TIMEOUT, DEFAULT_USER_AGENT

if TYPE_CHECKING:
    from blinkpy.auth import Auth
    from blinkpy.blinkpy import Blink

_LOGGER = logging.getLogger(__name__)

MIN_THROTTLE_TIME = 5


async def request_login(
    auth: Auth,
    url: str,
    login_data: dict,
    is_retry: bool = False,
) -> ClientResponse | dict | None:
    """
    Login request.

    :param auth: Auth instance.
    :param url: Login url.
    :param login_data: Dictionary containing blink login data.
    :param is_retry:
    """
    headers = {
        "Host": DEFAULT_URL,
        "Content-Type": "application/json",
        "user-agent": DEFAULT_USER_AGENT,
    }
    data = dumps(
        {
            "email": login_data["username"],
            "password": login_data["password"],
            "unique_id": login_data["uid"],
            "device_identifier": login_data["device_id"],
            "client_name": "Computer",
            "reauth": True,
        }
    )

    return await auth.query(
        url=url,
        headers=headers,
        data=data,
        json_resp=False,
        reqtype="post",
        is_retry=is_retry,
    )


async def request_verify(
    auth: Auth, blink: Blink, verify_key: str
) -> ClientResponse | None:
    """Send verification key to blink servers."""
    assert blink.urls is not None
    url = f"{blink.urls.base_url}/api/v4/account/{blink.account_id}/client/{blink.client_id}/pin/verify"
    data = dumps({"pin": verify_key})
    response = await auth.query(
        url=url,
        headers=auth.header,
        data=data,
        json_resp=False,
        reqtype="post",
    )
    if isinstance(response,ClientResponse):
        return response
    return None

async def request_logout(blink: Blink) -> dict | None:
    """Logout of blink servers."""
    assert blink.urls is not None
    url = f"{blink.urls.base_url}/api/v4/account/{blink.account_id}/client/{blink.client_id}/logout"
    response = await http_post(blink, url=url)
    if isinstance(response,dict):
        return response
    return None


async def request_networks(blink: Blink) -> dict | None:
    """Request all networks information."""
    assert blink.urls is not None
    url = f"{blink.urls.base_url}/networks"
    response = await http_get(blink, url)
    if isinstance(response,dict):
        return response
    return None


async def request_network_update(blink: Blink, network: str) -> dict | None:
    """
    Request network update.

    :param blink: Blink instance.
    :param network: Sync module network id.
    """
    assert blink.urls is not None
    url = f"{blink.urls.base_url}/network/{network}/update"
    response = await http_post(blink, url)
    if isinstance(response,dict):
        return response
    return None


async def request_user(blink: Blink) -> dict | None:
    """Get user information from blink servers."""
    assert blink.urls is not None
    url = f"{blink.urls.base_url}/user"
    response = await http_get(blink, url)
    if isinstance(response,dict):
        return response
    return None


async def request_network_status(blink: Blink, network: str) -> dict | None:
    """
    Request network information.

    :param blink: Blink instance.
    :param network: Sync module network id.
    """
    assert blink.urls is not None
    url = f"{blink.urls.base_url}/network/{network}"
    response = await http_get(blink, url)
    if isinstance(response,dict):
        return response
    return None


async def request_syncmodule(blink: Blink, network: str) -> dict | None:
    """
    Request sync module info.

    :param blink: Blink instance.
    :param network: Sync module network id.
    """
    assert blink.urls is not None
    url = f"{blink.urls.base_url}/network/{network}/syncmodules"
    response = await http_get(blink, url)
    if isinstance(response,dict):
        return response
    return None


@Throttle(seconds=MIN_THROTTLE_TIME)
async def request_system_arm(blink: Blink, network: str) -> dict | None:
    """
    Arm system.

    :param blink: Blink instance.
    :param network: Sync module network id.
    """
    assert blink.urls is not None
    url = f"{blink.urls.base_url}/api/v1/accounts/{blink.account_id}/networks/{network}/state/arm"
    response = await http_post(blink, url)
    if isinstance(response,dict):
        return response
    return None



@Throttle(seconds=MIN_THROTTLE_TIME)
async def request_system_disarm(blink: Blink, network: str) -> dict | None:
    """
    Disarm system.

    :param blink: Blink instance.
    :param network: Sync module network id.
    """
    assert blink.urls is not None
    url = f"{blink.urls.base_url}/api/v1/accounts/{blink.account_id}/networks/{network}/state/disarm"
    response = await http_post(blink, url)
    if isinstance(response,dict):
        return response
    return None



async def request_command_status(blink: Blink, network: str, command_id: str) -> dict | None:
    """
    Request command status.

    :param blink: Blink instance.
    :param network: Sync module network id.
    :param command_id: Command id to check.
    """
    assert blink.urls is not None
    url = f"{blink.urls.base_url}/network/{network}/command/{command_id}"
    response = await http_get(blink, url)
    if isinstance(response,dict):
        return response
    return None



@Throttle(seconds=MIN_THROTTLE_TIME)
async def request_homescreen(blink: Blink) -> dict | None:
    """Request homescreen info."""
    assert blink.urls is not None
    url = f"{blink.urls.base_url}/api/v3/accounts/{blink.account_id}/homescreen"
    response = await http_get(blink, url)
    if isinstance(response,dict):
        return response
    return None



@Throttle(seconds=MIN_THROTTLE_TIME)
async def request_sync_events(blink: Blink, network: str) -> dict | None:
    """
    Request events from sync module.

    :param blink: Blink instance.
    :param network: Sync module network id.
    """
    assert blink.urls is not None
    url = f"{blink.urls.base_url}/events/network/{network}"
    response = await http_get(blink, url)
    if isinstance(response,dict):
        return response
    return None



@Throttle(seconds=MIN_THROTTLE_TIME)
async def request_new_image(
    blink: Blink, network: str, camera_id: str
) ->  dict | None:
    """
    Request to capture new thumbnail for camera.

    :param blink: Blink instance.
    :param network: Sync module network id.
    :param camera_id: Camera ID of camera to request new image from.
    """
    assert blink.urls is not None
    url = f"{blink.urls.base_url}/network/{network}/camera/{camera_id}/thumbnail"
    response = await http_post(blink, url)
    if isinstance(response,dict):
        return response
    return None



@Throttle(seconds=MIN_THROTTLE_TIME)
async def request_new_video(
    blink: Blink, network: str, camera_id: str
) -> dict | None:
    """
    Request to capture new video clip.

    :param blink: Blink instance.
    :param network: Sync module network id.
    :param camera_id: Camera ID of camera to request new video from.
    """
    assert blink.urls is not None
    url = f"{blink.urls.base_url}/network/{network}/camera/{camera_id}/clip"
    response = await http_post(blink, url)
    if isinstance(response,dict):
        return response
    return None



@Throttle(seconds=MIN_THROTTLE_TIME)
async def request_video_count(blink: Blink) -> dict | None:
    """Request total video count."""
    assert blink.urls is not None
    url = f"{blink.urls.base_url}/api/v2/videos/count"
    response = await http_get(blink, url)
    if isinstance(response,dict):
        return response
    return None



async def request_videos(
    blink: Blink, time: float | None = None, page: int = 0
) -> dict | None:
    """
    Perform a request for videos.

    :param blink: Blink instance.
    :param time: Get videos since this time.  In epoch seconds.
    :param page: Page number to get videos from.
    """
    timestamp = get_time(time)
    assert blink.urls is not None
    url = f"{blink.urls.base_url}/api/v1/accounts/{blink.account_id}/media/changed?since={timestamp}&page={page}"
    response = await http_get(blink, url)
    if isinstance(response,dict):
        return response
    return None



async def request_cameras(blink: Blink, network: str) -> dict | None:
    """
    Request all camera information.

    :param Blink: Blink instance.
    :param network: Sync module network id.
    """
    assert blink.urls is not None
    url = f"{blink.urls.base_url}/network/{network}/cameras"
    response = await http_get(blink, url)
    if isinstance(response,dict):
        return response
    return None



async def request_camera_info(
    blink: Blink, network: str, camera_id: str
) -> dict | None:
    """
    Request camera info for one camera.

    :param blink: Blink instance.
    :param network: Sync module network id.
    :param camera_id: Camera ID of camera to request info from.
    """
    assert blink.urls is not None
    url = f"{blink.urls.base_url}/network/{network}/camera/{camera_id}/config"
    response = await http_get(blink, url)
    if isinstance(response,dict):
        return response
    return None



async def request_camera_usage(blink: Blink) -> dict | None:
    """
    Request camera status.

    :param blink: Blink instance.
    """
    assert blink.urls is not None
    url = f"{blink.urls.base_url}/api/v1/camera/usage"
    response = await http_get(blink, url)
    if isinstance(response,dict):
        return response
    return None



async def request_camera_liveview(
    blink: Blink, network: str, camera_id: str
) -> dict | None:
    """
    Request camera liveview.

    :param blink: Blink instance.
    :param network: Sync module network id.
    :param camera_id: Camera ID of camera to request liveview from.
    """
    assert blink.urls is not None
    url = f"{blink.urls.base_url}/api/v5/accounts/{blink.account_id}/networks/{network}/cameras/{camera_id}/liveview"
    response = await http_post(blink, url)
    if isinstance(response,dict):
        return response
    return None



async def request_camera_sensors(
    blink: Blink, network: str, camera_id: str
) -> dict | None:
    """
    Request camera sensor info for one camera.

    :param blink: Blink instance.
    :param network: Sync module network id.
    :param camera_id: Camera ID of camera to request sesnor info from.
    """
    assert blink.urls is not None
    url = f"{blink.urls.base_url}/network/{network}/camera/{camera_id}/signals"
    response = await http_get(blink, url)
    if isinstance(response,dict):
        return response
    return None


@Throttle(seconds=MIN_THROTTLE_TIME)
async def request_motion_detection_enable(
    blink: Blink, network: str, camera_id: str
) -> dict | None:
    """
    Enable motion detection for a camera.

    :param blink: Blink instance.
    :param network: Sync module network id.
    :param camera_id: Camera ID of camera to enable.
    """
    assert blink.urls is not None
    url = f"{blink.urls.base_url}/network/{network}/camera/{camera_id}/enable"
    response = await http_post(blink, url)
    if isinstance(response,dict):
        return response
    return None



@Throttle(seconds=MIN_THROTTLE_TIME)
async def request_motion_detection_disable(
    blink: Blink, network: str, camera_id: str
) -> dict | None:
    """Disable motion detection for a camera.

    :param blink: Blink instance.
    :param network: Sync module network id.
    :param camera_id: Camera ID of camera to disable.
    """
    assert blink.urls is not None
    url = f"{blink.urls.base_url}/network/{network}/camera/{camera_id}/disable"
    response = await http_post(blink, url)
    if isinstance(response,dict):
        return response
    return None


async def request_local_storage_manifest(
    blink: Blink, network: str, sync_id: str
) -> dict | None:
    """Request creation of an updated manifest of video clips stored in sync module local storage.

    :param blink: Blink instance.
    :param network: Sync module network id.
    :param sync_id: ID of sync module.
    """
    assert blink.urls is not None
    url = (
        f"{blink.urls.base_url}/api/v1/accounts/{blink.account_id}/networks/{network}/sync_modules/{sync_id}"
        + "/local_storage/manifest/request"
    )
    response = await http_post(blink, url)
    if isinstance(response,dict):
        return response
    return None



async def get_local_storage_manifest(
    blink: Blink, network: str, sync_id: str, manifest_request_id: str
) -> dict | None:
    """Request manifest of video clips stored in sync module local storage.

    :param blink: Blink instance.
    :param network: Sync module network id.
    :param sync_id: ID of sync module.
    :param manifest_request_id: Request ID of local storage manifest (requested creation of new manifest).
    """
    assert blink.urls is not None
    url = (
        f"{blink.urls.base_url}/api/v1/accounts/{blink.account_id}/networks/{network}/sync_modules/{sync_id}"
        + f"/local_storage/manifest/request/{manifest_request_id}"
    )
    response = await http_get(blink, url)
    if isinstance(response,dict):
        return response
    return None



async def request_local_storage_clip(
    blink: Blink, network: str, sync_id: str, manifest_id: str, clip_id: str
) -> dict | None:
    """Prepare video clip stored in the sync module to be downloaded.

    :param blink: Blink instance.
    :param network: Sync module network id.
    :param sync_id: ID of sync module.
    :param manifest_id: ID of local storage manifest (returned in the manifest response).
    :param clip_id: ID of the clip.
    """
    assert blink.urls is not None
    url = blink.urls.base_url + string.Template(
        local_storage_clip_url_template()
    ).substitute(
        account_id=blink.account_id,
        network_id=network,
        sync_id=sync_id,
        manifest_id=manifest_id,
        clip_id=clip_id,
    )
    response = await http_post(blink, url)
    if isinstance(response,dict):
        return response
    return None



async def request_get_config(
    blink: Blink, network: str, camera_id: str, product_type: str = "owl"
) -> dict | None:
    """Get camera configuration.

    :param blink: Blink instance.
    :param network: Sync module network id.
    :param camera_id: ID of camera
    :param product_type: Camera product type "owl" or "catalina"
    """
    assert blink.urls is not None
    if product_type == "owl":
        url = f"{blink.urls.base_url}/api/v1/accounts/{blink.account_id}/networks/{network}/owls/{camera_id}/config"
    elif product_type == "catalina":
        url = f"{blink.urls.base_url}/network/{network}/camera/{camera_id}/config"
    else:
        _LOGGER.info(
            "Camera %s with product type %s config get not implemented.",
            camera_id,
            product_type,
        )
        return None
    response = await http_get(blink, url)
    if isinstance(response,dict):
        return response
    return None



async def request_update_config(
    blink: Blink,
    network: str,
    camera_id: str,
    product_type: str = "owl",
    data: str | None = None,
) -> ClientResponse | None:
    """Update camera configuration.

    :param blink: Blink instance.
    :param network: Sync module network id.
    :param camera_id: ID of camera
    :param product_type: Camera product type "owl" or "catalina"
    :param data: string w/JSON dict of parameters/values to update
    """
    assert blink.urls is not None
    if product_type == "owl":
        url = f"{blink.urls.base_url}/api/v1/accounts/{blink.account_id}/networks/{network}/owls/{camera_id}/update"
    elif product_type == "catalina":
        url = f"{blink.urls.base_url}/network/{network}/camera/{camera_id}/update"
    else:
        _LOGGER.info(
            "Camera %s with product type %s config update not implemented.",
            camera_id,
            product_type,
        )
        return None
    response = await http_post(blink, url, json=False, data=data)
    if isinstance(response,ClientResponse):
        return response
    return None



async def http_get(
    blink: Blink,
    url: str,
    stream: bool = False,
    json: bool = True,
    is_retry: bool = False,
    timeout: int = TIMEOUT,
) -> ClientResponse | dict | None:
    """Perform an http get request.

    :param url: URL to perform get request.
    :param stream: Stream response? True/FALSE
    :param json: Return json response? TRUE/False
    :param is_retry: Is this part of a re-auth attempt?
    """
    _LOGGER.debug("Making GET request to %s", url)
    return await blink.auth.query(
        url=url,
        headers=blink.auth.header,
        reqtype="get",
        stream=stream,
        json_resp=json,
        is_retry=is_retry,
    )


async def http_post(
    blink: Blink,
    url: str,
    is_retry: bool = False,
    data: str | None = None,
    json: bool = True,
    timeout: int = TIMEOUT,
) -> ClientResponse | dict | None:
    """Perform an http post request.

    :param url: URL to perfom post request.
    :param is_retry: Is this part of a re-auth attempt?
    :param data: str body for post request
    :param json: Return json response? TRUE/False
    """
    _LOGGER.debug("Making POST request to %s", url)
    return await blink.auth.query(
        url=url,
        headers=blink.auth.header,
        reqtype="post",
        is_retry=is_retry,
        json_resp=json,
        data=data,
    )
