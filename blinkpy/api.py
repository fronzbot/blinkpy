"""Implements known blink API calls."""

import logging
import string
from json import dumps
from asyncio import sleep
from blinkpy.helpers.util import (
    get_time,
    Throttle,
    local_storage_clip_url_template,
)
from blinkpy.helpers.constants import DEFAULT_URL, TIMEOUT, DEFAULT_USER_AGENT

_LOGGER = logging.getLogger(__name__)

MIN_THROTTLE_TIME = 5
COMMAND_POLL_TIME = 1
MAX_RETRY = 120


async def request_login(
    auth,
    url,
    login_data,
    is_retry=False,
):
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


async def request_verify(auth, blink, verify_key):
    """Send verification key to blink servers."""
    url = (
        f"{blink.urls.base_url}/api/v4/account/{blink.account_id}"
        f"/client/{blink.client_id}/pin/verify"
    )
    data = dumps({"pin": verify_key})
    return await auth.query(
        url=url,
        headers=auth.header,
        data=data,
        json_resp=False,
        reqtype="post",
    )


async def request_logout(blink):
    """Logout of blink servers."""
    url = (
        f"{blink.urls.base_url}/api/v4/account/{blink.account_id}"
        f"/client/{blink.client_id}/logout"
    )
    return await http_post(blink, url=url)


async def request_networks(blink):
    """Request all networks information."""
    url = f"{blink.urls.base_url}/networks"
    return await http_get(blink, url)


async def request_network_update(blink, network):
    """
    Request network update.

    :param blink: Blink instance.
    :param network: Sync module network id.
    """
    url = f"{blink.urls.base_url}/network/{network}/update"
    response = await http_post(blink, url)
    await wait_for_command(blink, response)
    return response


async def request_user(blink):
    """Get user information from blink servers."""
    url = f"{blink.urls.base_url}/user"
    return await http_get(blink, url)


async def request_network_status(blink, network):
    """
    Request network information.

    :param blink: Blink instance.
    :param network: Sync module network id.
    """
    url = f"{blink.urls.base_url}/network/{network}"
    return await http_get(blink, url)


async def request_syncmodule(blink, network):
    """
    Request sync module info.

    :param blink: Blink instance.
    :param network: Sync module network id.
    """
    url = f"{blink.urls.base_url}/network/{network}/syncmodules"
    return await http_get(blink, url)


@Throttle(seconds=MIN_THROTTLE_TIME)
async def request_system_arm(blink, network, **kwargs):
    """
    Arm system.

    :param blink: Blink instance.
    :param network: Sync module network id.
    """
    url = (
        f"{blink.urls.base_url}/api/v1/accounts/{blink.account_id}"
        f"/networks/{network}/state/arm"
    )
    response = await http_post(blink, url)
    await wait_for_command(blink, response)
    return response


@Throttle(seconds=MIN_THROTTLE_TIME)
async def request_system_disarm(blink, network, **kwargs):
    """
    Disarm system.

    :param blink: Blink instance.
    :param network: Sync module network id.
    """
    url = (
        f"{blink.urls.base_url}/api/v1/accounts/{blink.account_id}"
        f"/networks/{network}/state/disarm"
    )
    response = await http_post(blink, url)
    await wait_for_command(blink, response)
    return response


async def request_command_status(blink, network, command_id):
    """
    Request command status.

    :param blink: Blink instance.
    :param network: Sync module network id.
    :param command_id: Command id to check.
    """
    url = f"{blink.urls.base_url}/network/{network}/command/{command_id}"
    return await http_get(blink, url)


@Throttle(seconds=MIN_THROTTLE_TIME)
async def request_homescreen(blink, **kwargs):
    """Request homescreen info."""
    url = f"{blink.urls.base_url}/api/v3/accounts/{blink.account_id}/homescreen"
    return await http_get(blink, url)


@Throttle(seconds=MIN_THROTTLE_TIME)
async def request_sync_events(blink, network, **kwargs):
    """
    Request events from sync module.

    :param blink: Blink instance.
    :param network: Sync module network id.
    """
    url = f"{blink.urls.base_url}/events/network/{network}"
    return await http_get(blink, url)


@Throttle(seconds=MIN_THROTTLE_TIME)
async def request_new_image(blink, network, camera_id, **kwargs):
    """
    Request to capture new thumbnail for camera.

    :param blink: Blink instance.
    :param network: Sync module network id.
    :param camera_id: Camera ID of camera to request new image from.
    """
    url = f"{blink.urls.base_url}/network/{network}/camera/{camera_id}/thumbnail"
    response = await http_post(blink, url)
    await wait_for_command(blink, response)
    return response


@Throttle(seconds=MIN_THROTTLE_TIME)
async def request_new_video(blink, network, camera_id, **kwargs):
    """
    Request to capture new video clip.

    :param blink: Blink instance.
    :param network: Sync module network id.
    :param camera_id: Camera ID of camera to request new video from.
    """
    url = f"{blink.urls.base_url}/network/{network}/camera/{camera_id}/clip"
    response = await http_post(blink, url)
    await wait_for_command(blink, response)
    return response


@Throttle(seconds=MIN_THROTTLE_TIME)
async def request_video_count(blink, **kwargs):
    """Request total video count."""
    url = f"{blink.urls.base_url}/api/v2/videos/count"
    return await http_get(blink, url)


async def request_videos(blink, time=None, page=0):
    """
    Perform a request for videos.

    :param blink: Blink instance.
    :param time: Get videos since this time.  In epoch seconds.
    :param page: Page number to get videos from.
    """
    timestamp = get_time(time)
    url = (
        f"{blink.urls.base_url}/api/v1/accounts/{blink.account_id}"
        f"/media/changed?since={timestamp}&page={page}"
    )
    return await http_get(blink, url)


async def request_cameras(blink, network):
    """
    Request all camera information.

    :param Blink: Blink instance.
    :param network: Sync module network id.
    """
    url = f"{blink.urls.base_url}/network/{network}/cameras"
    return await http_get(blink, url)


async def request_camera_info(blink, network, camera_id):
    """
    Request camera info for one camera.

    :param blink: Blink instance.
    :param network: Sync module network id.
    :param camera_id: Camera ID of camera to request info from.
    """
    url = f"{blink.urls.base_url}/network/{network}/camera/{camera_id}/config"
    return await http_get(blink, url)


async def request_camera_usage(blink):
    """
    Request camera status.

    :param blink: Blink instance.
    """
    url = f"{blink.urls.base_url}/api/v1/camera/usage"
    return await http_get(blink, url)


async def request_camera_liveview(blink, network, camera_id):
    """
    Request camera liveview.

    :param blink: Blink instance.
    :param network: Sync module network id.
    :param camera_id: Camera ID of camera to request liveview from.
    """
    url = (
        f"{blink.urls.base_url}/api/v5/accounts/{blink.account_id}"
        f"/networks/{network}/cameras/{camera_id}/liveview"
    )
    response = await http_post(blink, url)
    await wait_for_command(blink, response)
    return response


async def request_camera_sensors(blink, network, camera_id):
    """
    Request camera sensor info for one camera.

    :param blink: Blink instance.
    :param network: Sync module network id.
    :param camera_id: Camera ID of camera to request sensor info from.
    """
    url = f"{blink.urls.base_url}/network/{network}/camera/{camera_id}/signals"
    return await http_get(blink, url)


@Throttle(seconds=MIN_THROTTLE_TIME)
async def request_motion_detection_enable(blink, network, camera_id, **kwargs):
    """
    Enable motion detection for a camera.

    :param blink: Blink instance.
    :param network: Sync module network id.
    :param camera_id: Camera ID of camera to enable.
    """
    url = f"{blink.urls.base_url}/network/{network}/camera/{camera_id}/enable"
    response = await http_post(blink, url)
    await wait_for_command(blink, response)
    return response


@Throttle(seconds=MIN_THROTTLE_TIME)
async def request_motion_detection_disable(blink, network, camera_id, **kwargs):
    """
    Disable motion detection for a camera.

    :param blink: Blink instance.
    :param network: Sync module network id.
    :param camera_id: Camera ID of camera to disable.
    """
    url = f"{blink.urls.base_url}/network/{network}/camera/{camera_id}/disable"
    response = await http_post(blink, url)
    await wait_for_command(blink, response)
    return response


async def request_local_storage_manifest(blink, network, sync_id):
    """
    Update local manifest.

    Request creation of an updated manifest of video clips stored in
    sync module local storage.

    :param blink: Blink instance.
    :param network: Sync module network id.
    :param sync_id: ID of sync module.
    """
    url = (
        f"{blink.urls.base_url}/api/v1/accounts/{blink.account_id}"
        f"/networks/{network}/sync_modules/{sync_id}"
        f"/local_storage/manifest/request"
    )
    response = await http_post(blink, url)
    await wait_for_command(blink, response)
    return response


async def get_local_storage_manifest(blink, network, sync_id, manifest_request_id):
    """
    Request manifest of video clips stored in sync module local storage.

    :param blink: Blink instance.
    :param network: Sync module network id.
    :param sync_id: ID of sync module.
    :param manifest_request_id: Request ID of local storage manifest \
                                (requested creation of new manifest).
    """
    url = (
        f"{blink.urls.base_url}/api/v1/accounts/{blink.account_id}"
        f"/networks/{network}/sync_modules/{sync_id}"
        f"/local_storage/manifest/request/{manifest_request_id}"
    )
    return await http_get(blink, url)


async def request_local_storage_clip(blink, network, sync_id, manifest_id, clip_id):
    """
    Prepare video clip stored in the sync module to be downloaded.

    :param blink: Blink instance.
    :param network: Sync module network id.
    :param sync_id: ID of sync module.
    :param manifest_id: ID of local storage manifest (returned in manifest response).
    :param clip_id: ID of the clip.
    """
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
    await wait_for_command(blink, response)
    return response


async def request_get_config(blink, network, camera_id, product_type="owl"):
    """
    Get camera configuration.

    :param blink: Blink instance.
    :param network: Sync module network id.
    :param camera_id: ID of camera
    :param product_type: Camera product type "owl" or "catalina"
    """
    if product_type == "owl":
        url = (
            f"{blink.urls.base_url}/api/v1/accounts/{blink.account_id}"
            f"/networks/{network}/owls/{camera_id}/config"
        )
    elif product_type == "catalina":
        url = f"{blink.urls.base_url}/network/{network}/camera/{camera_id}/config"
    else:
        _LOGGER.info(
            "Camera %s with product type %s config get not implemented.",
            camera_id,
            product_type,
        )
        return None
    return await http_get(blink, url)


async def request_update_config(
    blink, network, camera_id, product_type="owl", data=None
):
    """
    Update camera configuration.

    :param blink: Blink instance.
    :param network: Sync module network id.
    :param camera_id: ID of camera
    :param product_type: Camera product type "owl" or "catalina"
    :param data: string w/JSON dict of parameters/values to update
    """
    if product_type == "owl":
        url = (
            f"{blink.urls.base_url}/api/v1/accounts/"
            f"{blink.account_id}/networks/{network}/owls/{camera_id}/config"
        )
    elif product_type == "catalina":
        url = f"{blink.urls.base_url}/network/{network}/camera/{camera_id}/update"
    else:
        _LOGGER.info(
            "Camera %s with product type %s config update not implemented.",
            camera_id,
            product_type,
        )
        return None
    return await http_post(blink, url, json=False, data=data)


async def http_get(
    blink, url, stream=False, json=True, is_retry=False, timeout=TIMEOUT
):
    """
    Perform an http get request.

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


async def http_post(blink, url, is_retry=False, data=None, json=True, timeout=TIMEOUT):
    """
    Perform an http post request.

    :param url: URL to perform post request.
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


async def wait_for_command(blink, json_data: dict) -> bool:
    """Wait for command to complete."""
    _LOGGER.debug("Command Wait %s", json_data)
    try:
        network_id = json_data.get("network_id")
        command_id = json_data.get("id")
    except AttributeError:
        return False
    if command_id and network_id:
        for _ in range(0, MAX_RETRY):
            _LOGGER.debug("Making GET request waiting for command")
            status = await request_command_status(blink, network_id, command_id)
            _LOGGER.debug("command status %s", status)
            if status:
                if status.get("status_code", 0) != 908:
                    return False
                if status.get("complete"):
                    return True
            await sleep(COMMAND_POLL_TIME)
