"""Implements known blink API calls."""

import logging
from json import dumps
import blinkpy.helpers.errors as ERROR
from blinkpy.helpers.util import http_req, get_time, BlinkException, Throttle
from blinkpy.helpers.constants import DEFAULT_URL

_LOGGER = logging.getLogger(__name__)

MIN_THROTTLE_TIME = 2


def request_login(blink, url, username, password, is_retry=False):
    """
    Login request.

    :param blink: Blink instance.
    :param url: Login url.
    :param username: Blink username.
    :param password: Blink password.
    :param is_retry: Is this part of a re-authorization attempt?
    """
    headers = {
        'Host': DEFAULT_URL,
        'Content-Type': 'application/json'
    }
    data = dumps({
        'email': username,
        'password': password,
        'client_specifier': 'iPhone 9.2 | 2.2 | 222'
    })
    return http_req(blink, url=url, headers=headers, data=data,
                    json_resp=False, reqtype='post', is_retry=is_retry)


def request_networks(blink):
    """Request all networks information."""
    url = "{}/networks".format(blink.urls.base_url)
    return http_get(blink, url)


def request_network_status(blink, network):
    """
    Request network information.

    :param blink: Blink instance.
    :param network: Sync module network id.
    """
    url = "{}/network/{}".format(blink.urls.base_url, network)
    return http_get(blink, url)


def request_syncmodule(blink, network):
    """
    Request sync module info.

    :param blink: Blink instance.
    :param network: Sync module network id.
    """
    url = "{}/network/{}/syncmodules".format(blink.urls.base_url, network)
    return http_get(blink, url)


@Throttle(seconds=MIN_THROTTLE_TIME)
def request_system_arm(blink, network):
    """
    Arm system.

    :param blink: Blink instance.
    :param network: Sync module network id.
    """
    url = "{}/network/{}/arm".format(blink.urls.base_url, network)
    return http_post(blink, url)


@Throttle(seconds=MIN_THROTTLE_TIME)
def request_system_disarm(blink, network):
    """
    Disarm system.

    :param blink: Blink instance.
    :param network: Sync module network id.
    """
    url = "{}/network/{}/disarm".format(blink.urls.base_url, network)
    return http_post(blink, url)


def request_command_status(blink, network, command_id):
    """
    Request command status.

    :param blink: Blink instance.
    :param network: Sync module network id.
    :param command_id: Command id to check.
    """
    url = "{}/network/{}/command/{}".format(blink.urls.base_url,
                                            network,
                                            command_id)
    return http_get(blink, url)


@Throttle(seconds=MIN_THROTTLE_TIME)
def request_homescreen(blink):
    """Request homescreen info."""
    url = "{}/api/v3/accounts/{}/homescreen".format(blink.urls.base_url,
                                                    blink.account_id)
    return http_get(blink, url)


@Throttle(seconds=MIN_THROTTLE_TIME)
def request_sync_events(blink, network):
    """
    Request events from sync module.

    :param blink: Blink instance.
    :param network: Sync module network id.
    """
    url = "{}/events/network/{}".format(blink.urls.base_url, network)
    return http_get(blink, url)


@Throttle(seconds=MIN_THROTTLE_TIME)
def request_new_image(blink, network, camera_id):
    """
    Request to capture new thumbnail for camera.

    :param blink: Blink instance.
    :param network: Sync module network id.
    :param camera_id: Camera ID of camera to request new image from.
    """
    url = "{}/network/{}/camera/{}/thumbnail".format(blink.urls.base_url,
                                                     network,
                                                     camera_id)
    return http_post(blink, url)


@Throttle(seconds=MIN_THROTTLE_TIME)
def request_new_video(blink, network, camera_id):
    """
    Request to capture new video clip.

    :param blink: Blink instance.
    :param network: Sync module network id.
    :param camera_id: Camera ID of camera to request new video from.
    """
    url = "{}/network/{}/camera/{}/clip".format(blink.urls.base_url,
                                                network,
                                                camera_id)
    return http_post(blink, url)


@Throttle(seconds=MIN_THROTTLE_TIME)
def request_video_count(blink):
    """Request total video count."""
    url = "{}/api/v2/videos/count".format(blink.urls.base_url)
    return http_get(blink, url)


def request_videos(blink, time=None, page=0):
    """
    Perform a request for videos.

    :param blink: Blink instance.
    :param time: Get videos since this time.  In epoch seconds.
    :param page: Page number to get videos from.
    """
    timestamp = get_time(time)
    url = "{}/api/v1/accounts/{}/media/changed?since={}&page={}".format(
        blink.urls.base_url, blink.account_id, timestamp, page)
    return http_get(blink, url)


def request_cameras(blink, network):
    """
    Request all camera information.

    :param Blink: Blink instance.
    :param network: Sync module network id.
    """
    url = "{}/network/{}/cameras".format(blink.urls.base_url, network)
    return http_get(blink, url)


def request_camera_info(blink, network, camera_id):
    """
    Request camera info for one camera.

    :param blink: Blink instance.
    :param network: Sync module network id.
    :param camera_id: Camera ID of camera to request info from.
    """
    url = "{}/network/{}/camera/{}/config".format(blink.urls.base_url,
                                                  network,
                                                  camera_id)
    return http_get(blink, url)


def request_camera_sensors(blink, network, camera_id):
    """
    Request camera sensor info for one camera.

    :param blink: Blink instance.
    :param network: Sync module network id.
    :param camera_id: Camera ID of camera to request sesnor info from.
    """
    url = "{}/network/{}/camera/{}/signals".format(blink.urls.base_url,
                                                   network,
                                                   camera_id)
    return http_get(blink, url)


@Throttle(seconds=MIN_THROTTLE_TIME)
def request_motion_detection_enable(blink, network, camera_id):
    """
    Enable motion detection for a camera.

    :param blink: Blink instance.
    :param network: Sync module network id.
    :param camera_id: Camera ID of camera to enable.
    """
    url = "{}/network/{}/camera/{}/enable".format(blink.urls.base_url,
                                                  network,
                                                  camera_id)
    return http_post(blink, url)


@Throttle(seconds=MIN_THROTTLE_TIME)
def request_motion_detection_disable(blink, network, camera_id):
    """Disable motion detection for a camera.

    :param blink: Blink instance.
    :param network: Sync module network id.
    :param camera_id: Camera ID of camera to disable.
    """
    url = "{}/network/{}/camera/{}/disable".format(blink.urls.base_url,
                                                   network,
                                                   camera_id)
    return http_post(blink, url)


def http_get(blink, url, stream=False, json=True, is_retry=False):
    """
    Perform an http get request.

    :param url: URL to perform get request.
    :param stream: Stream response? True/FALSE
    :param json: Return json response? TRUE/False
    :param is_retry: Is this part of a re-auth attempt?
    """
    if blink.auth_header is None:
        raise BlinkException(ERROR.AUTH_TOKEN)
    _LOGGER.debug("Making GET request to %s", url)
    return http_req(blink, url=url, headers=blink.auth_header,
                    reqtype='get', stream=stream, json_resp=json,
                    is_retry=is_retry)


def http_post(blink, url, is_retry=False):
    """
    Perform an http post request.

    :param url: URL to perfom post request.
    :param is_retry: Is this part of a re-auth attempt?
    """
    if blink.auth_header is None:
        raise BlinkException(ERROR.AUTH_TOKEN)
    _LOGGER.debug("Making POST request to %s", url)
    return http_req(blink, url=url, headers=blink.auth_header,
                    reqtype='post', is_retry=is_retry)
