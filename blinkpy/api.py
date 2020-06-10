"""Implements known blink API calls."""

import logging
from json import dumps
from blinkpy.helpers.util import get_time, Throttle
from blinkpy.helpers.constants import DEFAULT_URL

_LOGGER = logging.getLogger(__name__)

MIN_THROTTLE_TIME = 5


def request_login(
    auth, url, login_data, is_retry=False,
):
    """
    Login request.

    :param auth: Auth instance.
    :param url: Login url.
    :login_data: Dictionary containing blink login data.
    """
    headers = {"Host": DEFAULT_URL, "Content-Type": "application/json"}
    data = dumps(
        {
            "email": login_data["username"],
            "password": login_data["password"],
            "notification_key": login_data["notification_key"],
            "unique_id": login_data["uid"],
            "app_version": "6.0.7 (520300) #afb0be72a",
            "device_identifier": login_data["device_id"],
            "client_name": "Computer",
            "client_type": "android",
            "os_version": "5.1.1",
            "reauth": "true",
        }
    )
    return auth.query(
        url=url,
        headers=headers,
        data=data,
        json_resp=False,
        reqtype="post",
        is_retry=is_retry,
    )


def request_verify(auth, blink, verify_key):
    """Send verification key to blink servers."""
    url = f"{blink.urls.base_url}/api/v4/account/{blink.account_id}/client/{blink.client_id}/pin/verify"
    data = dumps({"pin": verify_key})
    return auth.query(
        url=url, headers=auth.header, data=data, json_resp=False, reqtype="post",
    )


def request_networks(blink):
    """Request all networks information."""
    url = f"{blink.urls.base_url}/networks"
    return http_get(blink, url)


def request_network_update(blink, network):
    """
    Request network update.

    :param blink: Blink instance.
    :param network: Sync module network id.
    """
    url = f"{blink.urls.base_url}/network/{network}/update"
    return http_post(blink, url)


def request_user(blink):
    """Get user information from blink servers."""
    url = f"{blink.urls.base_url}/user"
    return http_get(blink, url)


def request_network_status(blink, network):
    """
    Request network information.

    :param blink: Blink instance.
    :param network: Sync module network id.
    """
    url = f"{blink.urls.base_url}/network/{network}"
    return http_get(blink, url)


def request_syncmodule(blink, network):
    """
    Request sync module info.

    :param blink: Blink instance.
    :param network: Sync module network id.
    """
    url = f"{blink.urls.base_url}/network/{network}/syncmodules"
    return http_get(blink, url)


@Throttle(seconds=MIN_THROTTLE_TIME)
def request_system_arm(blink, network):
    """
    Arm system.

    :param blink: Blink instance.
    :param network: Sync module network id.
    """
    url = f"{blink.urls.base_url}/api/v1/accounts/{blink.account_id}/networks/{network}/state/arm"
    return http_post(blink, url)


@Throttle(seconds=MIN_THROTTLE_TIME)
def request_system_disarm(blink, network):
    """
    Disarm system.

    :param blink: Blink instance.
    :param network: Sync module network id.
    """
    url = f"{blink.urls.base_url}/api/v1/accounts/{blink.account_id}/networks/{network}/state/disarm"
    return http_post(blink, url)


def request_command_status(blink, network, command_id):
    """
    Request command status.

    :param blink: Blink instance.
    :param network: Sync module network id.
    :param command_id: Command id to check.
    """
    url = f"{blink.urls.base_url}/network/{network}/command/{command_id}"
    return http_get(blink, url)


@Throttle(seconds=MIN_THROTTLE_TIME)
def request_homescreen(blink):
    """Request homescreen info."""
    url = f"{blink.urls.base_url}/api/v3/accounts/{blink.account_id}/homescreen"
    return http_get(blink, url)


@Throttle(seconds=MIN_THROTTLE_TIME)
def request_sync_events(blink, network):
    """
    Request events from sync module.

    :param blink: Blink instance.
    :param network: Sync module network id.
    """
    url = f"{blink.urls.base_url}/events/network/{network}"
    return http_get(blink, url)


@Throttle(seconds=MIN_THROTTLE_TIME)
def request_new_image(blink, network, camera_id):
    """
    Request to capture new thumbnail for camera.

    :param blink: Blink instance.
    :param network: Sync module network id.
    :param camera_id: Camera ID of camera to request new image from.
    """
    url = f"{blink.urls.base_url}/network/{network}/camera/{camera_id}/thumbnail"
    return http_post(blink, url)


@Throttle(seconds=MIN_THROTTLE_TIME)
def request_new_video(blink, network, camera_id):
    """
    Request to capture new video clip.

    :param blink: Blink instance.
    :param network: Sync module network id.
    :param camera_id: Camera ID of camera to request new video from.
    """
    url = f"{blink.urls.base_url}/network/{network}/camera/{camera_id}/clip"
    return http_post(blink, url)


@Throttle(seconds=MIN_THROTTLE_TIME)
def request_video_count(blink):
    """Request total video count."""
    url = f"{blink.urls.base_url}/api/v2/videos/count"
    return http_get(blink, url)


def request_videos(blink, time=None, page=0):
    """
    Perform a request for videos.

    :param blink: Blink instance.
    :param time: Get videos since this time.  In epoch seconds.
    :param page: Page number to get videos from.
    """
    timestamp = get_time(time)
    url = f"{blink.urls.base_url}/api/v1/accounts/{blink.account_id}/media/changed?since={timestamp}&page={page}"
    return http_get(blink, url)


def request_cameras(blink, network):
    """
    Request all camera information.

    :param Blink: Blink instance.
    :param network: Sync module network id.
    """
    url = f"{blink.urls.base_url}/network/{network}/cameras"
    return http_get(blink, url)


def request_camera_info(blink, network, camera_id):
    """
    Request camera info for one camera.

    :param blink: Blink instance.
    :param network: Sync module network id.
    :param camera_id: Camera ID of camera to request info from.
    """
    url = f"{blink.urls.base_url}/network/{network}/camera/{camera_id}/config"
    return http_get(blink, url)


def request_camera_usage(blink):
    """
    Request camera status.

    :param blink: Blink instance.
    """
    url = f"{blink.urls.base_url}/api/v1/camera/usage"
    return http_get(blink, url)


def request_camera_liveview(blink, network, camera_id):
    """
    Request camera liveview.

    :param blink: Blink instance.
    :param network: Sync module network id.
    :param camera_id: Camera ID of camera to request liveview from.
    """
    url = (
        f"{blink.urls.base_url}/api/v3/networks/{network}/cameras/{camera_id}/liveview"
    )
    return http_post(blink, url)


def request_camera_sensors(blink, network, camera_id):
    """
    Request camera sensor info for one camera.

    :param blink: Blink instance.
    :param network: Sync module network id.
    :param camera_id: Camera ID of camera to request sesnor info from.
    """
    url = f"{blink.urls.base_url}/network/{network}/camera/{camera_id}/signals"
    return http_get(blink, url)


@Throttle(seconds=MIN_THROTTLE_TIME)
def request_motion_detection_enable(blink, network, camera_id):
    """
    Enable motion detection for a camera.

    :param blink: Blink instance.
    :param network: Sync module network id.
    :param camera_id: Camera ID of camera to enable.
    """
    url = f"{blink.urls.base_url}/network/{network}/camera/{camera_id}/enable"
    return http_post(blink, url)


@Throttle(seconds=MIN_THROTTLE_TIME)
def request_motion_detection_disable(blink, network, camera_id):
    """Disable motion detection for a camera.

    :param blink: Blink instance.
    :param network: Sync module network id.
    :param camera_id: Camera ID of camera to disable.
    """
    url = f"{blink.urls.base_url}/network/{network}/camera/{camera_id}/disable"
    return http_post(blink, url)


def http_get(blink, url, stream=False, json=True, is_retry=False):
    """
    Perform an http get request.

    :param url: URL to perform get request.
    :param stream: Stream response? True/FALSE
    :param json: Return json response? TRUE/False
    :param is_retry: Is this part of a re-auth attempt?
    """
    _LOGGER.debug("Making GET request to %s", url)
    return blink.auth.query(
        url=url,
        headers=blink.auth.header,
        reqtype="get",
        stream=stream,
        json_resp=json,
        is_retry=is_retry,
    )


def http_post(blink, url, is_retry=False):
    """
    Perform an http post request.

    :param url: URL to perfom post request.
    :param is_retry: Is this part of a re-auth attempt?
    """
    _LOGGER.debug("Making POST request to %s", url)
    return blink.auth.query(
        url=url, headers=blink.auth.header, reqtype="post", is_retry=is_retry
    )
